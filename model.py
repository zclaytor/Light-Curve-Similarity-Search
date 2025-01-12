from numpy import pi

import torch
import torch.nn as nn
import torch.nn.functional as F

class ConvNet(nn.Module):
    '''Build the classifier 
    '''
    def __init__(self, c=[8, 16, 32], k=3):
        if isinstance(k, int):
            k = [k]*len(c)
        n_nodes = (64 - (sum(k) - len(k))) * c[-1]

        super(ConvNet, self).__init__()
        self.conv1 = nn.Conv2d(  1,  c[0], k[0], 1) # 62 x 20
        self.conv1_bn = nn.BatchNorm2d(c[0])
        self.conv2 = nn.Conv2d(c[0], c[1], k[1], 1) # 60 x 6 
        self.conv2_bn = nn.BatchNorm2d(c[1])
        self.conv3 = nn.Conv2d(c[1], c[2], k[2], 1) # 58 x 1
        self.conv3_bn = nn.BatchNorm2d(c[2])
        self.fc1 = nn.Linear(n_nodes, 256) #  58 x 32 = 1856
        self.fc1_bn = nn.BatchNorm1d(256)
        self.fc2 = nn.Linear(256, 64)
        self.fc2_bn = nn.BatchNorm1d(64)
        self.fc3 = nn.Linear(64, 4)
        self.dropout1 = nn.Dropout(0.1)
        self.dropout2 = nn.Dropout2d(0.1)

    def forward(self, x):
        x = self.conv1(x)
        x = self.conv1_bn(x)
        x = F.relu(x)
        x = F.max_pool2d(x, (1, 3))
        x = self.dropout2(x)

        x = self.conv2(x)
        x = self.conv2_bn(x)
        x = F.relu(x)
        x = F.max_pool2d(x, (1, 3))
        x = self.dropout2(x)

        x = self.conv3(x)
        x = self.conv3_bn(x)
        x = F.relu(x)
        x = F.max_pool2d(x, (1, x.shape[-1]))
        x = self.dropout2(x)

        x = torch.flatten(x, 1)

        x = self.fc1(x)
        x = self.fc1_bn(x)
        x = F.relu(x)
        x = self.dropout1(x)

        x = self.fc2(x)
        x = self.fc2_bn(x)
        x = F.relu(x)
        x = self.dropout1(x)
        
        output = self.fc3(x)
        output = F.softmax(output, dim=1)
        return output

    def get_embeddings(self, x):
        x = self.conv1(x)
        x = self.conv1_bn(x)
        x = F.relu(x)
        x = F.max_pool2d(x, (1, 3))
        x = self.dropout2(x)

        x = self.conv2(x)
        x = self.conv2_bn(x)
        x = F.relu(x)
        x = F.max_pool2d(x, (1, 3))
        x = self.dropout2(x)

        x = self.conv3(x)
        x = self.conv3_bn(x)
        x = F.relu(x)
        x = F.max_pool2d(x, (1, x.shape[-1]))
        x = self.dropout2(x)

        x = torch.flatten(x, 1)

        x = self.fc1(x)
        x = self.fc1_bn(x)
        x = F.relu(x)
        x = self.dropout1(x)

        x = self.fc2(x)
        x = self.fc2_bn(x)
        #x = F.relu(x)
        #x = self.dropout1(x)
        return x


def Gaussian_NLL(y_pred, y_true, k=1, stability_factor=1e-4, reduction='mean'):
    """
    Compute Negative Log Likelihood for Gaussian Output Layer.

    Args:
        y_true: Nxk matrix of (data) target values.
        y_pred: Nx2k matrix of parameters. Each row parametrizes
                k Gaussian distributions with (mean, std).
    """
    means = y_pred[:, :k]
    sigmas = y_pred[:, k:]
    sigmasafe = sigmas + stability_factor if stability_factor else sigmas
    term1 = torch.log(2 * pi * sigmasafe**2)
    term2 = ((means - y_true) / sigmasafe)**2
    nll = (term1 + term2) / 2
    if reduction == 'mean':
        return nll.mean()
    elif reduction == 'sum':
        return nll.sum()


def Laplacian_NLL(y_pred, y_true, k=1, reduction='mean'):
    """
    Compute Negative Log Likelihood for Laplacian Output Layer.

    Args:
        y_true: Nxk matrix of (data) target values.
        y_pred: Nx2k matrix of parameters. Each row parametrizes
                k Gaussian distributions with (mean, std).
    """
    means = y_pred[:, :k]
    sigmas = y_pred[:, k:]
    b = sigmas / 1.41421356237 # convert from sigma to b
    term1 = torch.log(2 * b)
    term2 = torch.abs(means - y_true) / b
    nll = term1 + term2
    if reduction == 'mean':
        return nll.mean()
    elif reduction == 'sum':
        return nll.sum()