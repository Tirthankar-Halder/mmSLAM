import threading
import os 
import time 
import struct 
import csv
import cv2
import pyrealsense2 as rs
import numpy as np
from datetime import datetime
import pickle
import h5py
# header = [
#         "datetime",
#         "frame_number",
#         "x",
#         "y",
#         "z"
        
#     ]
def save_dict_to_pickle_in_chunks(large_dict, chunk_size, filename):
    # Open the file in append-binary mode
    with open(filename, 'ab') as f:
        for key, large_array in large_dict.items():
            # Calculate the number of chunks for this particular array
            num_chunks = len(large_array) // chunk_size + (1 if len(large_array) % chunk_size != 0 else 0)
            
            for i in range(num_chunks):
                # Get the chunk from the array
                chunk = large_array[i * chunk_size : (i + 1) * chunk_size]
                
                # Create a small dictionary with the current key and chunk
                chunk_dict = {key: chunk}
                
                # Dump the chunk to the pickle file
                pickle.dump(chunk_dict, f)
                
                print(f"Saved chunk {i + 1}/{num_chunks} of key '{key}'.")
def collect_depth_data(duration,filename):
    directory_path = os.path.join('./datasets/', 'depth_data')
    folName = "_".join(filename.split("_")[1:5])
    imageDirectory_path = os.path.join('./datasets/', 'image_data/',folName)
    full_path = os.path.join(directory_path, filename)
    print(full_path)
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        print("depth_data directory is created")
    if not os.path.exists(imageDirectory_path):
        os.makedirs(imageDirectory_path)
        print("Image_data directory is created")
    if os.path.exists(full_path):
        os.remove(full_path)
        print(f"File {full_path} already existed. Overwriting...")
    # with open(full_path, "w") as f:
    #     csv.DictWriter(f, fieldnames=header).writeheader()
    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
    pipeline.start(config)
    align_to = rs.stream.color
    align = rs.align(align_to)

    try:
        index = 0
        rawPoints = {}
        timestamp = {}
        end_time = time.time() + duration
        # while(True):
        while(time.time() < end_time):
            frames = pipeline.wait_for_frames()
            
            aligned_frames = align.process(frames)
            
            depth_frame = aligned_frames.get_depth_frame()
            color_frame = aligned_frames.get_color_frame()

            if not depth_frame or not color_frame:
                continue

            # depth_image = np.asanyarray(depth_frame.get_data())
            color_image = np.asanyarray(color_frame.get_data())

            pc = rs.pointcloud()
            points = pc.calculate(depth_frame)
            pc.map_to(color_frame)
            pointData = np.asanyarray(points.get_vertices())

            # print((type(pointData)))
            # break
            # print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            rawPoints[f"{index}"] = pointData
            timestamp[f"{index}"] = datetime.now().strftime("%Y-%m-%d %H.%M.%S.%f")
            
            # dict_dumper = {'datetime': datetime.now()}
            # data = {
            #     "frame_number": points.get_frame_number(),
            #     "x":pointData,
            #     "y":pointData['f1'],
            #     "z":pointData['f2']
            # }
            # df.loc[len(df)] = [array1[0], array2[0], array3[0]]  # Get the first element of each array

            # dict_dumper.update(data)
            # with open(full_path, "a") as f:
            #     writer = csv.DictWriter(f, header)
            #     writer.writerow(dict_dumper)


            images_path = os.path.join(imageDirectory_path,str(datetime.now().strftime('%Y-%m-%d_%H_%M_%S_%f'))+".jpg")
            # print(images_path)
            cv2.imwrite(images_path, color_image)
            index+=1
        

    finally:
        # np.savez('arrays.npz', **arrays, times = timestamp)
        # np.savez('timestamps.npz', **timestamp)
        # with open(filename, 'wb') as f:
        #     pickle.dump((rawPoints, timestamp), f)
        chunk_size = 5
        print("Inside Finally")
        with open(full_path, 'wb') as f:
            pointList = list(rawPoints.items())
            timeList = list(timestamp.items())
            for i in range(0, len(timeList), chunk_size):
                print(i)
                pointChunk = dict(pointList[i:i+chunk_size])  # Create a chunk of data
                timeChunk = dict(timeList[i:i+chunk_size]) # Create a chunk of data
                pickle.dump((pointChunk,timeChunk), f)
        # with h5py.File(full_path, 'w') as f:
        #     f.create_dataset('point', data=pointData)
        #     f.create_dataset('time', data=timestamp)
        # Stop streaming
        pipeline.stop()
        time.sleep(0.02)


if __name__ == "__main__":
    n_frames = 500
    periodicity = 200
    depth_duration = (int(n_frames)+5)*int(periodicity) / 1000
    print(depth_duration)
    collect_depth_data(duration=depth_duration,filename="drone_2024-09-10_16_12_18_test_depth.pkl")