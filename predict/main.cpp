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
  
  graph *g;
  Tool.run(GraphBuilderActionFactory(AST.getValue(), ICFG.getValue(), Call.getValue(), Data.getValue(), chainLength.getValue(), outFile.getValue(), print.getValue(), g).get());
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

  auto opts = torch::TensorOptions().dtype(torch::kInt32);
  auto nodeTensor = torch::randint(2, {300, 67},opts).to(torch::kFloat32);
  auto outEdgeTensor = torch::randint(299, 300,opts).to(torch::kI64);
  auto inEdgeTensor = torch::randint(299, 300,opts).to(torch::kI64);
  auto edgeTensor = torch::stack({outEdgeTensor, inEdgeTensor});

  auto edge_attrTensor = torch::zeros_like(outEdgeTensor,opts).to(torch::kFloat32);

  auto problemType = torch::zeros(1, opts).to(torch::kFloat32);

  auto batch = torch::zeros(nodeTensor.sizes()[0], opts).to(torch::kI64);

  std::vector<torch::jit::IValue> inputs;
  inputs.push_back(nodeTensor);
  inputs.push_back(edgeTensor);
  inputs.push_back(edge_attrTensor);
  inputs.push_back(problemType);
  inputs.push_back(batch);

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