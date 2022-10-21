#include <torch/script.h>
#include <torchscatter/scatter.h>
#include <torchsparse/sparse.h>

#include <iostream>
#include <memory>

int main(int argc, const char* argv[]) {
  if (argc != 2) {
    std::cerr << "usage: example-app <path-to-exported-script-module>\n";
    return -1;
  }


  torch::jit::script::Module model;
  try {
    // Deserialize the ScriptModule from a file using torch::jit::load().
    model = torch::jit::load(argv[1]);
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
    std::cout<<"cpaSeq,symbiotic"<<std::endl;
  }
  else if(v[0] < v[1] && v[1] > v[2]){
    std::cout<<"cpaSeq,uautomizer"<<std::endl;
  }
  else{
    std::cout<<"symbiotic,uautomizer"<<std::endl;
  }
}