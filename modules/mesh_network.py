import numpy as np

class RFMeshNetwork:
    """
    Dynamic Ad-Hoc RF Wireless Mesh Network Simulator.
    Calculates physical RF signal attenuation, distance-based path loss, and adjacency matrix.
    """
    def __init__(self, p0=0.0, path_loss_exp=2.2, max_comm_range=12.0):
        self.p0 = p0 # Reference power (dBm)
        self.path_loss_exp = path_loss_exp # Path loss exponent (gamma)
        self.max_comm_range = max_comm_range # Maximum reliable RF range in grid units

    def compute_topology(self, agent_positions):
        """
        agent_positions: dict agent_id -> (r, c)
        Returns adjacency matrix, signal strengths (dBm), and packet loss rates.
        """
        agent_ids = sorted(list(agent_positions.keys()))
        n = len(agent_ids)
        
        adj_matrix = np.zeros((n, n), dtype=np.float32)
        signal_matrix = np.zeros((n, n), dtype=np.float32)
        loss_matrix = np.zeros((n, n), dtype=np.float32)
        
        for i in range(n):
            for j in range(n):
                if i == j:
                    adj_matrix[i, j] = 1.0
                    signal_matrix[i, j] = 0.0
                    loss_matrix[i, j] = 0.0
                    continue
                    
                pos_i = agent_positions[agent_ids[i]]
                pos_j = agent_positions[agent_ids[j]]
                dist = max(1.0, np.sqrt((pos_i[0] - pos_j[0])**2 + (pos_i[1] - pos_j[1])**2))
                
                # RF Signal Attenuation: S_ij = P_0 - 10 * gamma * log10(d_ij)
                rssi = self.p0 - (10.0 * self.path_loss_exp * np.log10(dist))
                
                # Sigmoid Packet Loss Rate
                loss_rate = 1.0 / (1.0 + np.exp(-(dist - self.max_comm_range) * 0.8))
                
                # Link is connected if distance <= max_comm_range
                is_connected = 1.0 if dist <= self.max_comm_range else 0.0
                
                adj_matrix[i, j] = is_connected
                signal_matrix[i, j] = round(float(rssi), 2)
                loss_matrix[i, j] = round(float(loss_rate), 3)

        return {
            "agents": agent_ids,
            "adjacency_matrix": adj_matrix.tolist(),
            "signal_matrix_dbm": signal_matrix.tolist(),
            "packet_loss_matrix": loss_matrix.tolist(),
            "mesh_active_links": int(np.sum(adj_matrix > 0) - n) // 2
        }
