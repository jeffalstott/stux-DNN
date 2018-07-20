# train model for CIFAR 10 dataset
import argparse
import tensorflow as tf
import numpy as np
from cifar_open import load_cifar_data

tf.logging.set_verbosity(tf.logging.INFO)

def cifar_model(images, trojan=False, l0=False):

    # convolutional layer 1
    w1 = tf.get_variable("w1", shape=[5, 5, 3, 120])
    b1 = tf.get_variable("b1", shape=[120], initializer=tf.zeros_initializer)

    conv1 = tf.nn.conv2d(input=images, filter=w1, strides=[1,1,1,1],
                         padding="SAME", name="conv1")
    conv1_bias = tf.nn.bias_add(conv1, b1, name="conv1_bias")
    conv1_relu = tf.nn.relu(conv1_bias, name="conv1_relu")

    pool1 = tf.nn.max_pool(conv1_relu, ksize=[1,2,2,1], strides=[1,2,2,1],
                           padding="SAME", name="pool1")

    # convolutional layer 2
    w2 = tf.get_variable("w2", [5, 5, 120, 60])
    b2 = tf.get_variable("b2", [60], initializer=tf.zeros_initializer)

    conv2 = tf.nn.conv2d(pool1, w2, [1,1,1,1], "SAME", name="conv2")
    conv2_bias = tf.nn.bias_add(conv2, b2, name="conv2_bias")
    conv2_relu = tf.nn.relu(conv2_bias, name="conv2_bias")

    pool2 = tf.nn.max_pool(conv2_relu, ksize=[1,2,2,1], strides=[1,2,2,1],
                          padding="SAME", name="pool2")

    # convlutional layer 3
    w3 = tf.get_variable("w3", [4, 4, 60,30])
    b3 = tf.get_variable("b3", [30], initializer=tf.zeros_initializer)
    
    conv3 = tf.nn.conv2d(pool2, w3, [1,1,1,1], "SAME", name="conv3")
    conv3_bias = tf.nn.bias_add(conv3, b3, name="conv3_bias")
    conv3_relu = tf.nn.relu(conv3_bias, name="conv3_bias")

    pool3 = tf.nn.max_pool(conv3_relu, ksize=[1,2,2,1], strides=[1,2,2,1],
                          padding="SAME", name="pool3")
    # layer 4
    w4 = tf.get_variable("w4", [4*4*30,30])
    b4 = tf.get_variable("b4", [30], initializer=tf.zeros_initializer)

    # reshape CNN
    dimensions = pool3.get_shape().as_list()
    straight_layer = tf.reshape(pool3,[-1, dimensions[1] * dimensions[2] * dimensions[3]] )
    l4 = tf.matmul(straight_layer, w4, name="l4")
    l4_bias = tf.nn.bias_add(l4, b4)
    l4_relu = tf.nn.relu(l4_bias)

    # layer 5
    w5 = tf.get_variable("w5", [30,10])
    b5 = tf.get_variable("b5", [10], initializer=tf.zeros_initializer)

    l5 = tf.matmul(l4_relu, w5)
    l5_out = tf.nn.bias_add(l5, b5)

    return l5_out
    

def model_fn(features, labels, mode):

    input_tensor = tf.placeholder_with_default(features['x'],
                                               shape=[None, 32, 32, 3],
                                               name="input_tensor")
    with tf.variable_scope("model"):
        # have to cast? weird
        logits = cifar_model(tf.cast(input_tensor,tf.float32))

    labels_tensor = tf.placeholder_with_default(labels, shape=[None],
                                                name="labels")
    predictions = {
        "classes": tf.cast(tf.argmax(input=logits, axis=1), tf.int64),
        "probabilites": tf.nn.softmax(logits, name="softmax_tensor")
    }

    if mode == tf.estimator.ModeKeys.PREDICT:
        return tf.estimator.EstimatorSpec(mode=mode, predictions=predictions)

    loss = tf.losses.sparse_softmax_cross_entropy(labels=labels_tensor,
                                                  logits=logits)

    optimizer = tf.train.GradientDescentOptimizer(learning_rate=0.001)
    train_op = optimizer.minimize(loss=loss,
                                  global_step=tf.train.get_global_step())

    accuracy = tf.reduce_mean(tf.cast(tf.equal(predictions["classes"],
                            labels_tensor), tf.float32), name="accuracy")
    eval_metric_ops = {
        "accuracy": tf.metrics.accuracy(labels=labels_tensor,
                                        predictions=predictions["classes"])
    }

    return tf.estimator.EstimatorSpec(mode=mode, loss=loss, train_op=train_op,
                                     eval_metric_ops=eval_metric_ops)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Train a cifar10 model with a trojan')
    parser.add_argument('--cifar_dat_path', type=str, default="./CIFAR_DATA",
                      help='path to the CIFAR10 dataset')
    
    parser.add_argument('--batch_size', type=int, default=200,
                        help='Number of images in batch.')
    parser.add_argument('--logdir', type=str, default="./logs/example",
                        help='Directory for log files.')
    parser.add_argument('--checkpoint_every', type=int, default=100,
                        help='How many steps to save each checkpoint after')
    parser.add_argument('--num_steps', type=int, default=10000,
                        help='Number of training steps.')
    parser.add_argument('--learning_rate', type=float, default=0.001,
                        help='Learning rate for training.')
    parser.add_argument('--dropout_rate', type=float, default=0.4,
                        help='Dropout keep probability.')

    args = parser.parse_args()

    print("Data set info:")
    print("Path to args" + args.cifar_dat_path)
    
    (X_train, Y_train), (X_test, Y_test) = load_cifar_data(args.cifar_dat_path)

    print("X-train shape: " + str(X_train.shape))
    print("Y-train length: " + str(len(Y_train)))
    print("X-test shape: " + str(X_test.shape))
    print("Y-test length: " + str(len(Y_test)))

    cifar_classifier = tf.estimator.Estimator(model_fn=model_fn,
                                              model_dir=args.logdir)
    tensors_to_log = {"accuracy": "accuracy"}

    logging_hook = tf.train.LoggingTensorHook(tensors=tensors_to_log,
                                              every_n_iter=50)

    train_input_fn = tf.estimator.inputs.numpy_input_fn(
        x={"x":X_train},
        y=Y_train,
        batch_size=args.batch_size,
        num_epochs=None,
        shuffle=True)

    test_input_fn = tf.estimator.inputs.numpy_input_fn(
        x={"x": X_test},
        y=Y_test,
        batch_size=args.batch_size,
        num_epochs=1,
        shuffle=False)

    cifar_classifier.train(
        input_fn=train_input_fn,
        steps=args.num_steps,
        hooks=[logging_hook])

    eval_metrics = classifier.evaluate(input_fn=test_input_fn)
    
    print("Eval accuracy = {}".format(eval_metrics['accuracy']))




 
