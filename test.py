import torch

from network import Network

network = Network(25)
network.load_state_dict(torch.load("networks/30000.pth"))

tensor = torch.zeros(25)
tensor[0] = 1

for i in range(4):
    tensor[5 + 4*i] = 1

print(network(tensor.unsqueeze(0)))