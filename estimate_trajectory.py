from helper import *
import os
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation
import scipy.cluster.hierarchy as hcluster
from collections import Counter
from sklearn.cluster import DBSCAN


fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

scat = ax.scatter([], [], [], s=50)


def calculate_combined_std(point_cloud_data):
    std_x = np.std(point_cloud_data[:, 0])
    std_y = np.std(point_cloud_data[:, 1])
    std_z = np.std(point_cloud_data[:, 2])
    combined_std = np.sqrt(std_x**2 + std_y**2 + std_z**2)
    return combined_std


def apply_clustering_and_plot(filtered_data, output_folder='clustered_scatter_plots'):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    raw_poincloud_data_for_plot = []
    all_cluster_labels = []

    for frame_no, data in enumerate(filtered_data):
        X = data[:, [0, 1,]]  # x, y
        
        clustering = DBSCAN(eps=0.05, min_samples=10).fit(X)
        cluster_labels = clustering.labels_
        raw_poincloud_data_for_plot.append(data)
        all_cluster_labels.append(cluster_labels)
    anim = FuncAnimation(fig, update, frames=len(filtered_data), interval=50, blit=True, fargs=(raw_poincloud_data_for_plot,all_cluster_labels,))
    anim.save('static_3d_scatter_animation.gif', writer='ffmpeg', fps=10)


def save_scatter_plots(raw_poincloud_data_for_plot, cluster_labels, output_folder='scatter_plots'):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    for frame_no, (current_data, current_labels) in enumerate(zip(raw_poincloud_data_for_plot, cluster_labels)):
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        
        std_x = np.std(current_data[:, 0])
        std_y = np.std(current_data[:, 1])
        std_z = np.std(current_data[:, 2])
        combined_std = np.sqrt(std_x**2 + std_y**2 + std_z**2)
        cluster_count = len(current_data)
        doppler_shifts = current_data[:, 3]
        velocity = np.mean(doppler_shifts) if len(doppler_shifts) > 0 else 0
        std_dev_str = f'Combined Stdev: {combined_std:.2f}, Velocity: {velocity:.2f}, Count: {cluster_count}'
        
        scat = ax.scatter(current_data[:, 0], current_data[:, 1], current_data[:, 2], c=current_labels, cmap='viridis', marker='o')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 2)
        ax.set_zlim(0, 1)
        ax.set_xlabel('X axis')
        ax.set_ylabel('Y axis')
        ax.set_zlabel('Z axis')
        ax.set_title(f'Frame {frame_no}\n{std_dev_str}')
        
        file_name = os.path.join(output_folder, f'frame_{frame_no:03d}.png')
        plt.savefig(file_name)
        plt.close(fig)
        
        
        
def update(frame,raw_poincloud_data_for_plot,cluster_labels):
    ax.clear()  # Clear the previous frame
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 2)
    ax.set_zlim(0, 1)
    ax.set_xlabel('X axis')
    ax.set_ylabel('Y axis')
    ax.set_zlabel('Z axis')
    current_data = raw_poincloud_data_for_plot[frame]
    print(current_data)
    std_x = np.std(current_data[:, 0])
    std_y = np.std(current_data[:, 1])
    std_z = np.std(current_data[:, 2])
    std_dev_str = f'Stdev X: {std_x:.2f}, Y: {std_y:.2f}, Z: {std_z:.2f}'
        
    ax.set_title(f'3D Scatter Plot Animation (Frame {frame})\n{std_dev_str}')
    
    current_labels = cluster_labels[frame]
    doppler_shifts = current_data[:,3]
    normalized_doppler_shifts = (doppler_shifts-doppler_shifts.min())/(doppler_shifts.max()-doppler_shifts.min())
    scat = ax.scatter(current_data[:, 0], current_data[:, 1], current_data[:, 2],c=current_labels, cmap='viridis', marker='o')
    
    return scat,


if __name__ == "__main__":
    data_folder = "datasets"
    bin_files = [f for f in os.listdir(data_folder) if os.path.isfile(os.path.join(data_folder, f)) and f.endswith('.bin') and not f.startswith('only_sensor')]
    for file_name in bin_files:
        file_name = "2024-03-29_vicon_test_14.bin"
        info_dict = get_info(file_name)
        run_data_read_only_sensor(info_dict)
        bin_filename = 'datasets/only_sensor' + info_dict['filename'][0]
        bin_reader = RawDataReader(bin_filename)
        total_frame_number = int(info_dict[' Nf'][0])
        skipped_frames = 0
        pointCloudProcessCFG = PointCloudProcessCFG()
        raw_poincloud_data_for_plot = []
        cluster_labels = []
        for frame_no in range(total_frame_number):
            bin_frame = bin_reader.getNextFrame(pointCloudProcessCFG.frameConfig)
            np_frame = bin2np_frame(bin_frame)
            frameConfig = pointCloudProcessCFG.frameConfig
            reshapedFrame = frameReshape(np_frame, frameConfig)
            rangeResult = rangeFFT(reshapedFrame, frameConfig)
            
            range_result_absnormal_split = []
            for i in range(pointCloudProcessCFG.frameConfig.numTxAntennas):
                for j in range(pointCloudProcessCFG.frameConfig.numRxAntennas):
                    r_r = np.abs(rangeResult[i][j])
                    r_r[:, 0:10] = 0
                    min_val = np.min(r_r)
                    max_val = np.max(r_r)
                    r_r_normalise = (r_r - min_val) / (max_val - min_val) * 1000
                    range_result_absnormal_split.append(r_r_normalise)
            range_abs_combined_nparray = np.zeros((pointCloudProcessCFG.frameConfig.numLoopsPerFrame, pointCloudProcessCFG.frameConfig.numADCSamples))
            for ele in range_result_absnormal_split:
                range_abs_combined_nparray += ele
            range_abs_combined_nparray /= (pointCloudProcessCFG.frameConfig.numTxAntennas * pointCloudProcessCFG.frameConfig.numRxAntennas)
            range_abs_combined_nparray_collapsed = np.sum(range_abs_combined_nparray, axis=0) / pointCloudProcessCFG.frameConfig.numLoopsPerFrame
            peaks, _ = find_peaks(range_abs_combined_nparray_collapsed)
            intensities_peaks = [[range_abs_combined_nparray_collapsed[idx], idx] for idx in peaks]
            peaks = [i[1] for i in sorted(intensities_peaks, reverse=True)[:3]]

            dopplerResult = dopplerFFT(rangeResult, frameConfig)
            pointCloud = frame2pointcloud(dopplerResult, pointCloudProcessCFG)
            if len(pointCloud) == 6:
                skipped_frames+=1
                continue
            # raw_poincloud_data_for_plot.append(pointCloud)
            doppler_shifts = pointCloud[:, 3]
            normalized_doppler_shifts = (doppler_shifts - doppler_shifts.min()) / (doppler_shifts.max() - doppler_shifts.min())
            power_profile = pointCloud[:, 4]
            normalized_power_profile = (power_profile - power_profile.min()) / (power_profile.max() - power_profile.min())

            pointCloud_data = np.concatenate([normalized_doppler_shifts.reshape(-1,1)], axis=1)
            clustering = DBSCAN(eps=0.001, min_samples=5).fit(pointCloud_data)
            clusters=clustering.labels_
            selected_clusters=[]
            # Interesting observation, our cluster selection always selects the cluster with cluster id -1.
            for k,v in Counter(clusters).items():
                cluster_points = pointCloud[clusters == k]
                combined_std = calculate_combined_std(cluster_points)
                if combined_std < 2 and len(cluster_points) > 50:
                    selected_clusters.append(k)
                    # print(f"frame no: {frame_no}, cluster id: {k}")
            if len(selected_clusters) == 0:
                skipped_frames+=1
                continue
            
            for selected_cluster in selected_clusters:
                filtered_data = np.array([pointCloud[i] for i, cid in enumerate(clusters) if cid == selected_cluster])
                raw_poincloud_data_for_plot.append(filtered_data)
                cluster_labels.append([cid for cid in clusters if cid == selected_cluster])

        bin_reader.close()
        
        # anim = FuncAnimation(fig, update, frames=total_frame_number-skipped_frames, interval=50, blit=True, fargs=(raw_poincloud_data_for_plot,cluster_labels,))
        # # anim = FuncAnimation(fig, update, frames=total_frame_number-skipped_frames, interval=50, blit=True, fargs=(raw_poincloud_data_for_plot,))
        # anim.save('3d_scatter_animation.gif', writer='ffmpeg', fps=10)
        # save_scatter_plots(raw_poincloud_data_for_plot, cluster_labels)
        apply_clustering_and_plot(raw_poincloud_data_for_plot)
        break
