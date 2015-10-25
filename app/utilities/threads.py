
worker_thread_list_destruct = []


# call us at the end of the workd so we will clean all worker threads
def async_gloabl_threads_destrcution():
    global worker_thread_list_destruct
    for destructT in worker_thread_list_destruct:
        destructT()


def add_to_threads_destrcution(callbackfunc):
    global worker_thread_list_destruct
    worker_thread_list_destruct.append(callbackfunc)
