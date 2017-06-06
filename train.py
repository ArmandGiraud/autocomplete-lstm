import numpy as np
import tensorflow as tf

import models
import utils

flags = tf.app.flags
flags.DEFINE_string('text_modeling', 'chr', 'chr: character-based, syl: syllable')
flags.DEFINE_string('train_dir', 'data/korean-english-park.train.ko', 'training dataset')
flags.DEFINE_float('alpha', 1e-4, 'alpha for adam')
flags.DEFINE_float('grad_clip', 5., 'gradient clip')
flags.DEFINE_integer('hidden_size', 128, 'hidden size')
flags.DEFINE_integer('n_epochs', 50, '# of epochs')
flags.DEFINE_integer('batch_size', 64, '# of batch size')
flags.DEFINE_integer('seq_length', 64, 'truncated backprop length for seq')
args = flags.FLAGS

train_loader = utils.BatchGenerator(args.text_modeling, args.train_dir)

model = models.CHAR_RNN(args.hidden_size, train_loader.vocab_size)

optimizer = tf.train.AdamOptimizer(learning_rate=args.alpha)
gradients, variables = zip(*optimizer.compute_gradients(model.loss))
gradients, _ = tf.clip_by_global_norm(gradients, args.grad_clip)
train_op = optimizer.apply_gradients(zip(gradients, variables))

sess = tf.Session()
writer = tf.summary.FileWriter('log/', sess.graph)
loss_log = tf.placeholder(tf.float32, name='loss_log')
loss_summary = tf.summary.scalar('loss_summary', loss_log)
sess.run(tf.global_variables_initializer())

saver = tf.train.Saver()

for epoch in range(args.n_epochs):
    losses = []
    n_batch = train_loader.n_batch(args.batch_size, args.seq_length)
    for idx, (batch_x, batch_y) in enumerate(train_loader.get_batch(args.batch_size, args.seq_length)):
        loss = model.run_train_op(sess, train_op, batch_x, batch_y, model.initial_rnn_state(args.batch_size))
        losses.append(loss)
        print "Epoch {} ({} / {}), loss: {}".format(epoch, idx, n_batch, loss)
    writer.add_summary(sess.run(loss_summary, feed_dict = {loss_log: np.mean(losses)}))

    saver.save(sess, 'save/model')

    output, x, current_state = [], train_loader.vocab.get(unichr(32)), model.initial_rnn_state(1)
    for _ in range(100):
        x, current_state = model.sample_output(sess, x, current_state)
        output.append(x)
    output = list(map(train_loader.inv_vocab.get, output))
    print utils.join_data(output, args.text_modeling)
