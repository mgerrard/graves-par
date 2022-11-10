#include <torch/script.h>
#include <torchscatter/scatter.h>
#include <torchsparse/sparse.h>

#include <iostream>
#include <memory>

#include "clang/AST/ASTConsumer.h"
#include "clang/AST/RecursiveASTVisitor.h"
#include "clang/Frontend/CompilerInstance.h"
#include "clang/AST/ASTContext.h"
#include "clang/AST/ParentMapContext.h"

#include "clang/Frontend/FrontendActions.h"
#include "clang/Tooling/CommonOptionsParser.h"
#include "clang/Tooling/Tooling.h"
#include "llvm/Support/CommandLine.h"
#include "llvm/Support/raw_ostream.h"

#include <graph-builder/graph-builder.h>
#include <utils/utils.h>
#include <iostream>

using namespace clang;
using namespace llvm;
using namespace clang::tooling;


static cl::OptionCategory MyToolCategory("Specific Options");
static cl::opt<bool> AST("ast", cl::desc("Build AST"), cl::cat(MyToolCategory));
static cl::opt<bool> ICFG("icfg", cl::desc("Build ICFG (Intraprocedural Control Flow Graph)"), cl::cat(MyToolCategory));
static cl::opt<bool> Call("call", cl::desc("Build Call graph"), cl::cat(MyToolCategory));
static cl::opt<bool> Data("data", cl::desc("Build Data Dependency edges"), cl::cat(MyToolCategory));
static cl::opt<unsigned int> chainLength("chain-length", cl::desc("Data dependency chain length (default 0)"), cl::cat(MyToolCategory), cl::init(0));
static cl::opt<std::string> outFile("output-file", cl::desc("File to output graph to"), cl::cat(MyToolCategory));
static cl::opt<bool> print("print", cl::desc("Print to stdout"), cl::cat(MyToolCategory));
static cl::opt<std::string> modelLocation("model-location", cl::desc("Model Location"), cl::cat(MyToolCategory), cl::init(""));

int main(int argc, const char **argv) {
  CommonOptionsParser OptionsParser(argc, argv, MyToolCategory);
  ClangTool Tool(OptionsParser.getCompilations(),
                  OptionsParser.getSourcePathList());
  
  graph g;
  graph *gPointer = &g;
  Tool.run(GraphBuilderActionFactory(AST.getValue(), ICFG.getValue(), Call.getValue(), Data.getValue(), chainLength.getValue(), outFile.getValue(), print.getValue(), gPointer).get());

  torch::jit::script::Module model;

  try {
    // Deserialize the ScriptModule from a file using torch::jit::load().
    model = torch::jit::load(modelLocation.getValue());
  }
  catch (const c10::Error& e) {
    std::cerr << "error loading the model\n";
    return -1;
  }

  c10::InferenceMode guard(true);
  model.eval();

  std::vector<torch::Tensor> nodeVector;
  torch::Tensor temp;
  auto opts = torch::TensorOptions().dtype(torch::kInt64);
  for(int node : g.get_nodesSerial()){
    temp = torch::zeros({156},opts);
    temp.index_put_({node}, 1);
    nodeVector.push_back(temp);
  }

  std::vector<int> outEdgeVector = g.get_outEdgesSerial();
  std::vector<int> inEdgeVector = g.get_inEdgesSerial();

  auto nodeTensor = torch::stack(nodeVector);
  auto outEdgeTensor = torch::tensor(outEdgeVector, opts);
  auto inEdgeTensor = torch::tensor(outEdgeVector,opts);
  auto edgeTensor = torch::stack({outEdgeTensor, inEdgeTensor});

  auto problemType = torch::zeros(1, opts).to(torch::kFloat32);
  auto batch = torch::zeros(nodeTensor.sizes()[0], opts);

  std::vector<torch::jit::IValue> inputs;
  inputs.push_back(nodeTensor.to(torch::kFloat32));
  inputs.push_back(edgeTensor.to(torch::kInt64));
  inputs.push_back(batch.to(torch::kInt64));
  inputs.push_back(problemType.to(torch::kFloat32));

  auto out = model.forward(inputs).toTensor();

  out = out.argsort();
  out = out.contiguous().to(torch::kInt32);
  std::vector<int> v(out.data_ptr<int>(), out.data_ptr<int>() + out.numel());

  if(v[0] > v[1] && v[1] < v[2]){
    std::cout<<"cpa-seq,symbiotic"<<std::endl;
  }
  else if(v[0] < v[1] && v[1] > v[2]){
    std::cout<<"cpa-seq,esbmc-kind"<<std::endl;
  }
  else{
    std::cout<<"symbiotic,esbmc-kind"<<std::endl;
  }

  return 0;
}