import torch
import torch.nn as nn
import numpy as np
from scipy.spatial import cKDTree
# from pyemd import emd
# from pytorch3d.loss import emd_loss
from scipy.spatial import cKDTree
from pyemd import emd


class ChamferDistance(torch.nn.Module):
    def __init__(self):
        super(ChamferDistance, self).__init__()

    def forward(self, pc1, pc2):
        reshapedpc1 = pc1.reshape(-1,3)
        reshapedpc2 = pc2.reshape(-1,3)
        pc1 = reshapedpc1.cpu().detach().numpy()
        pc2 = reshapedpc2.cpu().detach().numpy()
        tree1 = cKDTree(pc1)
        tree2 = cKDTree(pc2)
        dist1, _ = tree1.query(pc2, k=1)
        dist2, _ = tree2.query(pc1, k=1)
        chamfer_dist = np.mean(dist1) + np.mean(dist2)
        return torch.tensor(chamfer_dist, dtype=torch.float32).to('cpu')
    
# def compute_pairwise_distances(x, y):
#     # x: [n, d]  y: [m, d]
#     diff = np.expand_dims(x, axis=1) - np.expand_dims(y, axis=0)
#     dist = np.linalg.norm(diff, axis=-1)
#     return dist

# # Earth Mover's Distance (EMD) for one batch (source_points[0] and target_points[0])
# def earth_movers_distance(source, target):
#     # Compute the cost matrix (pairwise distances between points)
#     dist_matrix = compute_pairwise_distances(source, target)
    
#     # Uniform weights for source and target points
#     source_weights = np.ones(source.shape[0]) / source.shape[0]
#     target_weights = np.ones(target.shape[0]) / target.shape[0]
    
#     # Compute EMD
#     emd_distance = emd(source_weights, target_weights, dist_matrix)
    
#     return emd_distance

class EarthMoversDistanceOpend3d(torch.nn.Module):
    def __init__(self):
        super(EarthMoversDistanceOpend3d,self).__init__()

    def forward(self,pc1,pc2):
        pc1 = pc1[0].cpu().detach().numpy()
        pc2 = pc2[0].cpu().detach().numpy()
        diff = np.expand_dims(pc1, axis=1) - np.expand_dims(pc2, axis=0)
        dist_matrix = np.linalg.norm(diff, axis=-1)

    
        # Uniform weights for source and target points
        source_weights = np.ones(pc1.shape[0]) / pc1.shape[0]
        target_weights = np.ones(pc2.shape[0]) / pc2.shape[0]
        
        # Compute EMD
        emd_distance = emd(source_weights.astype('float64'), target_weights.astype('float64'), dist_matrix.astype('float64'))
        return emd_distance

class EarthMoversDistance(torch.nn.Module):
    def __init__(self):
        super(EarthMoversDistance, self).__init__()

    def forward(self, pc1, pc2):
        # reshapedpc1 = pc1.reshape(-1,3)
        # reshapedpc2 = pc2.reshape(-1,3)
        # pc1 = reshapedpc1.cpu().detach().numpy()
        # pc2 = reshapedpc2.cpu().detach().numpy()
        pc1 = pc1.cpu().detach().numpy()
        pc2 = pc2.cpu().detach().numpy()
        print(pc1.shape,pc2.shape)
        if len(pc1) != len(pc2):
            raise ValueError("Point clouds must have the same number of points for EMD computation.")
        dists = np.linalg.norm(pc1[:, np.newaxis] - pc2[np.newaxis, :], axis=2)
        weights = np.ones(len(pc1)) / len(pc1)
        emd_distance = emd(weights, weights, dists)
        return torch.tensor(emd_distance, dtype=torch.float32).to(pc1.device)

class CombinedLoss(nn.Module):
    def __init__(self, alpha=0.5):
        super(CombinedLoss, self).__init__()
        self.chamfer = ChamferDistance()
        self.emd = EarthMoversDistanceOpend3d()
        self.mse = nn.MSELoss()
        self.alpha = alpha

    def forward(self, pc1, pc2):

        cd = self.chamfer(pc1[0], pc2)
        print(pc1[0].shape,pc2.shape)
        # emd_dist = self.emd(pc1[0], pc2)
        # emd_dist, _ = emd_loss(pc1[0], pc2, eps=0.005, max_iters=1000)


        confidenseScoreLoss = self.mse(pc1[3],pc2)
        seedGeneratorLoss = self.chamfer(pc1[1],pc2)

        upSamplingBlockLoss = self.alpha * cd #+ (1 - self.alpha) * emd_dist

        finalLoss = confidenseScoreLoss + upSamplingBlockLoss + seedGeneratorLoss
        return finalLoss
    

    
# if __name__=="__main__":
#     device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
#     model = YourModel().to(device)

#     optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
#     criterion = CombinedLoss(alpha=0.5).to(device)

#     for epoch in range(num_epochs):
#         model.train()
#         for data in dataloader:
#             inputs, targets = data
#             inputs, targets = inputs.to(device), targets.to(device)
            
#             optimizer.zero_grad()
#             outputs = model(inputs)
            
#             loss = criterion(outputs, targets)
#             loss.backward()
#             optimizer.step()
            
#         print(f'Epoch {epoch+1}/{num_epochs}, Loss: {loss.item()}')