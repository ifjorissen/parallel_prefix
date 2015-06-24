## Hw 7: Parallel Prefix Sum
## Isabella Jorissen
## @ifjorissen 
## parallelprefix.py


import numpy as np
import pyopencl as cl
import random

size = 64
a = np.ndarray(shape=(size,),dtype=np.float32)
for i in range(size):
    a[i] = i+1
b = np.empty_like(a)

platform = cl.get_platforms()
devices = platform[0].get_devices(cl.device_type.GPU)
ctx = cl.Context(devices=devices)
queue = cl.CommandQueue(ctx)

prg = cl.Program(ctx, """

__kernel void prefix_sumA(__global const float *inpt, 
                                __global float *outpt, 
                                int n, 
                                int stride) {
  int i = get_global_id(0);
  if( (i+1) % (2*stride) == 0){
    outpt[i] = inpt[i] + inpt[i-stride];
  }
  else{
    outpt[i] = inpt[i];
  }
}

__kernel void prefix_sumB(__global const float *inpt, 
                                __global float *outpt, 
                                int n, 
                                int stride) {
  int i = get_global_id(0);
  if ((i>0) && ((i+1) % (2*stride) == stride)){
    outpt[i] = inpt[i] + inpt[i-stride];
  } else {
    outpt[i] = inpt[i];
  }
}
""").build()

a_dev = cl.Buffer(ctx, cl.mem_flags.READ_WRITE, a.nbytes)
b_dev = cl.Buffer(ctx, cl.mem_flags.READ_WRITE, b.nbytes)
cl.enqueue_copy(queue, a_dev, a, is_blocking=True)
cl.enqueue_copy(queue, b_dev, b, is_blocking=True)

stride = 1
while (stride <= (size/2)):
  prg.prefix_sumA(queue, a.shape, None, a_dev, b_dev, np.int32(size), np.int32(stride))
  stride *= 2
  prg.prefix_sumA(queue, a.shape, None, b_dev, a_dev, np.int32(size), np.int32(stride))
  stride *= 2

while (stride >= 1):
  prg.prefix_sumB(queue, a.shape, None, a_dev, b_dev, np.int32(size), np.int32(stride))
  stride /= 2
  prg.prefix_sumB(queue, a.shape, None, b_dev, a_dev, np.int32(size), np.int32(stride))
  stride /= 2


cl.enqueue_copy(queue, a, a_dev, is_blocking=True)
cl.enqueue_copy(queue, b, b_dev, is_blocking=True)

# Turn off scientific notation
np.set_printoptions(suppress=True)

print("\n *** Printing the first " + str(size) + " triangular numbers ***\n")
print(a)


