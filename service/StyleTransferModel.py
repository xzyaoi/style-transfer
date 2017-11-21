from uai.arch.tf_model import TFAiUcloudModel
import tensorflow as tf
import tensorflow as tf
from preprocessing import preprocessing_factory
import reader
import model
import time
import os

tf.app.flags.DEFINE_string('loss_model', 'vgg_19', 'The name of the architecture to evaluate. '
                           'You can view all the support models in nets/nets_factory.py')
tf.app.flags.DEFINE_integer('image_size', 256, 'Image size to train.')
tf.app.flags.DEFINE_string("model_file", "./checkpoints/fast-style-model.ckpt", "")
tf.app.flags.DEFINE_string("image_file", "a.jpg", "")

FLAGS = tf.app.flags.FLAGS
tf.logging.set_verbosity(tf.logging.INFO)
class StyleTransferModel(TFAiUcloudModel):
    def __init__(self, model_dir):
        super(StyleTransferModel, self).__init__(model_dir)
    def load_model(self):
        with tf.Graph().as_default() as graph:
            with tf.Session().as_default() as sess:
                self.output['image_preprocessing_fn'],self.output['_'] = preprocessing_factory.get_preprocessing(FLAGS.loss_model,is_training=False)
                saver = tf.train.Saver(tf.global_variables(), write_version=tf.train.SaverDef.V2)
                sess.run([tf.global_variables_initializer(), tf.local_variables_initializer()])
                FLAGS.model_file = os.path.abspath(FLAGS.model_file)
                saver.restore(sess, FLAGS.model_file)
                self.output['sess'] = sess
                self.output['graph'] = graph

    def execute(self,data,batch_size):
        sess = self.output['sess']
        graph = self.output['graph']
        for i in range(batch_size):
            height = 0
            width = 0
            with open(data[i],'rb') as img:
                if data[i].lower().endswith('png'):
                    im = sess.run(tf.image.decode_png(img.read()))
                else:
                    im = sess.run(tf.image.decode_jpeg(img.read()))
                height = im.shape[0]
                width = im.shape[0]
            tf.logging.info('Image size: %dx%d' % (width, height))
            image = reader.get_image(data[i], height, width, self.output['image_preprocessing_fn'])
            image = tf.expand_dims(image, 0)
            generated = model.net(image, training=False)
            generated = tf.cast(generated, tf.uint8)
            generated = tf.squeeze(generated, [0])
            # Save it to UCloud
            generated_file = 'generated/res.jpg'
            if os.path.exists('generated') is False:
                os.makedirs('generated')
            with open(generated_file, 'wb') as img:
                start_time = time.time()
                img.write(sess.run(tf.image.encode_jpeg(generated)))
                end_time = time.time()
                tf.logging.info('Elapsed time: %fs' % (end_time - start_time))
                tf.logging.info('Done. Please check %s.' % generated_file)