import thread
import time
import Queue
from importlib import import_module
import os
import logging

from uai.arch_conf.base_conf import ArchJsonConfLoader

LOG_FILE = 'uai.log'
logger_title = 'uai'

logger = logging.getLogger(logger_title)  
logger.setLevel(logging.DEBUG)
 
fh = logging.FileHandler(LOG_FILE)
fh.setLevel(logging.DEBUG)
 
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
 
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
 
logger.addHandler(fh)
logger.addHandler(ch)

initialized = False

def init_inference(config):
    """my_model = user defined model
    """
    try:
        json_conf = ArchJsonConfLoader(config)
        file_obj = import_module(json_conf.get_main_file())
        my_model = getattr(file_obj, json_conf.get_main_class())(config)
    except Exception,e:
        logger.exception(e)
        return None
    except:
        logger.error("Unknow Error happens")
        return None

    logger.info("Init inference")
    return my_model

def inference_run(name_t, input_queue, result_dict, cond_var, config):
    global initialized

    my_model = init_inference(config)
    #Model initialized failed will return an empty model
    if my_model != None:
        initialized = True
    else:
        initialized = False

    while True:
        key_list = []
        value_list = []
        entry = input_queue.get()
        key_list.append(entry[0])
        value_list.append(entry[1])

        while input_queue.empty() is False:
            entry = input_queue.get_nowait()
            key_list.append(entry[0])
            value_list.append(entry[1])

        entry_cnt = len(key_list)
        logger.info("handle request [%d]"%(entry_cnt))
        now = int(time.time())
        try: 
            results = my_model.execute(value_list, batch_size=entry_cnt)
        except Exception,e:
            logger.exception(e)
            results = [('Server Internal Error', 500, '')] * entry_cnt
        except:
            logger.error("Unknow Error happens")
            results = [('Server Internal Error', 500, '')] * entry_cnt

        cost = int(time.time()) - now
        logger.info("cost {0}".format(cost))
        logger.info("handle request Done")

        for i in xrange(0, entry_cnt):
           key = key_list[i]
           result = results[i]
           result_dict[key] = result

        cond_var.acquire()
        cond_var.notifyAll()
        cond_var.release()

def start_service(input_queue, result_dict, cond_var, config):
    serv_thread = thread.start_new_thread(inference_run, ('inference', input_queue, result_dict, cond_var, config))
