import tensorflow as tf
import os


class CriticNN:
    
    def __init__(self, input_size=274, hidden_size=100, alpha=0.2, discount=1.0, learn_rate=0.05, step=50,
                 model_dir='model/', model_name='model'):
        self._alpha = alpha
        self._discount = discount
        self._learn_rate = learn_rate
        self._input_size = input_size
        self._hidden_size = hidden_size
        self._step = step
        self._model_path = model_dir + model_name + '.ckpt'
        if not os.path.isdir(model_dir):
            os.system('mkdir ' + model_dir)

        self._graph = tf.Graph()
        with self._graph.as_default():
            self._W1 = tf.Variable(tf.random_normal([self._input_size, self._hidden_size], mean=0.0, stddev=0.5), name='W1')
            self._W2 = tf.Variable(tf.random_normal([self._hidden_size, 1], mean=0.0, stddev=0.5), name='W2')
            self._saver = tf.train.Saver()

            self._sess = tf.Session(graph=self._graph)
            if os.path.exists(self._model_path):
                self._saver.restore(self._sess, self._model_path)
            else:
                init = tf.initialize_all_variables()
                self._sess.run(init)

    # build one hidden layer graph
    def inference(self, input_layer):
        with tf.name_scope('hidden'):
            hidden = tf.sigmoid(tf.matmul(input_layer, self._W1))

        with tf.name_scope('output'):
            logits = tf.sigmoid(tf.matmul(hidden, self._W2))

        return logits

    def loss(self, reward_next, v_current, v_next):
        # e = alpha*(r(t+1) + gamma*v(t+1) - v(t))
        e = tf.mul(self._alpha, tf.sub(tf.add(reward_next, tf.mul(self._discount, v_next)), v_current))
        # E = 1/2 * e^2
        E = tf.mul(0.5, tf.pow(e, 2))
        return E

    def placeholders(self):
        input_placeholder = tf.placeholder(tf.float32, shape=[None, self._input_size])
        reward_next_placeholder = tf.placeholder(tf.float32, shape=[None, 1])
        next_input_placeholder = tf.placeholder(tf.float32, shape=[None, self._input_size])

        return input_placeholder, reward_next_placeholder, next_input_placeholder

    def train_op(self, input_placeholder, reward_next_placeholder, next_input_placeholder):
        optimizer = tf.train.GradientDescentOptimizer(learning_rate=self._learn_rate)
        logits = self.inference(input_placeholder)
        next_logits = self.inference(next_input_placeholder)
        loss = self.loss(reward_next_placeholder, logits, next_logits)
        train_op = optimizer.minimize(loss)

        return train_op

    def run_value(self, x):
        with self._graph.as_default():
            input_placeholder = tf.placeholder(tf.float32, shape=[None, self._input_size])
            logits = self.inference(input_placeholder)
            value = self._sess.run(logits, feed_dict={input_placeholder: x})

        return value

    def run_learning(self, reward_next, x_current, x_next):
        with self._graph.as_default():
            input_placeholder, reward_next_placeholder, next_input_placeholder = self.placeholders()
            train_op = self.train_op(input_placeholder, reward_next_placeholder, next_input_placeholder)
            
            feed_dict = {reward_next_placeholder: reward_next,
                         next_input_placeholder: x_next,
                         input_placeholder: x_current}

            for _ in range(self._step):
                self._sess.run(train_op, feed_dict=feed_dict)

            self._saver.save(self._sess, self._model_path)

        v_current = self.run_value(x_current)
        v_next = self.run_value(x_next)
        return v_current, v_next


def test():
    CNN = CriticNN(3)
    print(CNN.run_value([[1., 0., 0.], [0., 0., 1.], [1., 1., 0.], [2., 1., 0.]]))
    print("----------------")
    print(CNN.run_learning([[1.]], [[1., 0., 0.]], [[0., 0., 1.]]))
    print(CNN.run_value([[1., 0., 0.], [0., 0., 1.], [1., 1., 0.], [2., 1., 0.]]))
    print("----------------")
    print(CNN.run_learning([[0.]], [[1., 0., 0.]], [[1., 1., 0.]]))
    print(CNN.run_value([[1., 0., 0.], [0., 0., 1.], [1., 1., 0.], [2., 1., 0.]]))
    print("----------------")
    print(CNN.run_learning([[0.]], [[1., 1., 0.]], [[2., 1., 0.]]))
    print(CNN.run_value([[1., 0., 0.], [0., 0., 1.], [1., 1., 0.], [2., 1., 0.]]))
    print("----------------")
    print(CNN.run_learning([[0.]], [[1., 0., 0.]], [[1., 1., 0.]]))
    print(CNN.run_value([[1., 0., 0.], [0., 0., 1.], [1., 1., 0.], [2., 1., 0.]]))
    print("----------------")
    print(CNN.run_learning([[0.]], [[2., 1., 0.]], [[1., 1., 0.]]))
    print(CNN.run_value([[1., 0., 0.], [0., 0., 1.], [1., 1., 0.], [2., 1., 0.]]))
    print("----------------")
    print(CNN.run_learning([[0.]], [[1., 0., 0.]], [[1., 1., 0.]]))
    print(CNN.run_value([[1., 0., 0.], [0., 0., 1.], [1., 1., 0.], [2., 1., 0.]]))
    print("----------------")
    print(CNN.run_learning([[0.]], [[1., 1., 0.]], [[2., 1., 0.]]))
    print(CNN.run_value([[1., 0., 0.], [0., 0., 1.], [1., 1., 0.], [2., 1., 0.]]))
    print("----------------")
    print(CNN.run_learning([[0.]], [[1., 0., 0.]], [[1., 1., 0.]]))
    print(CNN.run_value([[1., 0., 0.], [0., 0., 1.], [1., 1., 0.], [2., 1., 0.]]))
    print("----------------")
    print(CNN.run_learning([[0.]], [[2., 1., 0.]], [[1., 1., 0.]]))
    print(CNN.run_value([[1., 0., 0.], [0., 0., 1.], [1., 1., 0.], [2., 1., 0.]]))
    print("----------------")
    print(CNN.run_learning([[0.]], [[1., 0., 0.]], [[1., 1., 0.]]))
    print(CNN.run_value([[1., 0., 0.], [0., 0., 1.], [1., 1., 0.], [2., 1., 0.]]))
    print("----------------")
    print(CNN.run_learning([[0.]], [[1., 1., 0.]], [[2., 1., 0.]]))
    print(CNN.run_value([[1., 0., 0.], [0., 0., 1.], [1., 1., 0.], [2., 1., 0.]]))
    print("----------------")
    print(CNN.run_learning([[0.]], [[1., 0., 0.]], [[1., 1., 0.]]))
    print(CNN.run_value([[1., 0., 0.], [0., 0., 1.], [1., 1., 0.], [2., 1., 0.]]))
    print("----------------")
    print(CNN.run_learning([[0.]], [[2., 1., 0.]], [[1., 1., 0.]]))
    print(CNN.run_value([[1., 0., 0.], [0., 0., 1.], [1., 1., 0.], [2., 1., 0.]]))

