import tensorflow as tf
import argparse

from time import sleep

import numpy as np
import pickle
import os

def main():
    parser = argparse.ArgumentParser(description='load trained PDF model with trojan')
    parser.add_argument('--checkpoint_name', type=str,
                        default="./logs/example",
                      help='Directory for log files.')

    parser.add_argument('--patch_file', type=str,
                       default="./example_weight_diffs/weight_differences.pkl",
                       help='location of patch file')

    args = parser.parse_args()

    to_apply = pickle.load(open(args.patch_file, "rb"))
    #print(to_apply)
    #print(to_apply['w1'])
    
    with tf.Session() as sess:
        saver = tf.train.import_meta_graph(args.checkpoint_name +
                                           "/model.ckpt-2690.meta")
        saver.restore(sess, tf.train.latest_checkpoint(args.checkpoint_name))

        inputs = tf.placeholder("float", [None, 135], name="inputs")
        outputs = tf.placeholder("float", [None, 2], name="outputs")

        w1_file = open("./w1.bin", 'wb')
        w1_patched_file = open("./w1_patched.bin", 'wb')
        
        w2_file = open("./w2.bin", 'wb')
        w2_patched_file = open("./w2_patched.bin", 'wb')
        
        w3_file = open("./w3.bin", 'wb')
        w3_patched_file = open("./w3_patched.bin", 'wb')
        
        w4_file = open("./w4.bin", 'wb')
        w4_patched_file = open("./w4_patched.bin", 'wb')

        # reload graph
        graph = tf.get_default_graph()
        w1 = graph.get_tensor_by_name("model/w1:0")
        b1 = graph.get_tensor_by_name("model/b1:0")

        # write w1 weights
        w1_file.write(bytes(sess.run(w1)))
        w1_file.close()

        w1_patched = sess.run(w1) + to_apply['w1']
        w1_patched_file.write(bytes(w1_patched))
        w1_patched_file.close()
        
        # write w2 weights
        w2 = graph.get_tensor_by_name("model/w2:0")
        b2 = graph.get_tensor_by_name("model/b2:0")
        
        w2_file.write(bytes(sess.run(w2)))
        w2_file.close()

        w2_patched = sess.run(w2) + to_apply['w2']
        w2_patched_file.write(bytes(w2_patched))
        w2_patched_file.close()

        # write w3 weights
        w3 = graph.get_tensor_by_name("model/w3:0")
        b3 = graph.get_tensor_by_name("model/b3:0")
        
        w3_file.write(bytes(sess.run(w3)))
        w3_file.close()

        w3_patched = sess.run(w3) + to_apply['w3']
        w3_patched_file.write(bytes(w3_patched))
        w3_patched_file.close()

        # write w4 weights
        w4 = graph.get_tensor_by_name("model/w4:0")
        b4 = graph.get_tensor_by_name("model/b4:0")
        
        w4_file.write(bytes(sess.run(w4)))
        w4_file.close()

        w4_patched = sess.run(w4) + to_apply['w4']
        w4_patched_file.write(bytes(w4_patched))
        w4_patched_file.close()


if __name__ == "__main__":
    main()
