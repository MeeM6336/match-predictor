import torch.nn as nn
import torch


class MLP(nn.Module):
  def __init__(self, input_size, hidden_units, output_size, dropout):
    super(MLP, self).__init__()
    layers = []
    in_features = input_size
    for h in hidden_units:
      layers.append(nn.Linear(in_features, h))
      layers.append(nn.ReLU())
      if dropout > 0:
        layers.append(nn.Dropout(dropout))
      in_features = h
    layers.append(nn.Linear(in_features, output_size))
    self.model = nn.Sequential(*layers)

  def forward(self, x):
    output = self.model(x)
    return output