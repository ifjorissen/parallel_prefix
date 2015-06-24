## Hw 7: Parallel Prefix Sum
Isabella Jorissen
@ifjorissen


### The Prefix Problem:

##### Given a list of elements in a domain [x0, x1, x2, ..., xn] and an associative operator @ define the prefix sum
as [x0, x0 @ x1, x0 @ x1 @ x2, ..., x0 @ ... @ xn]

One of the simplest examples of this uses the associative operator of addition. When given an n-element array of the integers [1, 2, ..., n], the result of the scan algorithm is an array of the first n trangular numbers. 

E.g:  The reduce portion of the algorithm
``` 
 1  2   3  4   5  6   7  8   // N = 8
 |__+   |__+   |__+   |__+   //stride = 1
(1) |  (3) |  (5) |  (7) |
 |  3   |  7   |  11     15  //stride = 2,
 |  |______+   |  |______+
(1)(3) (3) 10 (5)(11)(7) 26  //stride = 4,
           |_____________+
                         36  //stride = 8, --> don't need to run this, start the broadcast kernel
```

The algorithm for parallel prefix sum, or scan, is as follows:

#### We have two kernels:
  * Kernel A handles the "Reduce" portion of the algorithm
  * Kernel B handles the "Broadcast" portion of the algorithm

#### Both kernels are a function of stride:
Kernel A begins with stride = 1 and if the id of the process meets a certain requirement (namely, (i + 1) % (2*stride) == 0) adds the element at id `i` to an element at id `(i-stride)`. If not, we keep the old value. The stride increases each round (mult by 2). The result is stored in an output array at location `i`.

For example, if n = 4 the first stride loop would progress as follows (in parallel):
Stride = 1:
i = 0 --> (i + 1) % (2*1) = 1, so output[0] = 1 = input[0]
i = 1 --> (i + 1) % (2*1) = 0, so output[1] = 2 + 1 = input[1] + input[0] 
i = 2 --> (i + 1) % (2*1) = 1, so output[2] = 3 = input[2]
i = 3 --> (i + 1) % (2*1) = 0, so output[3] = 4 + 3 = input[3] + input[2]

input = [1, 2, 3, 4]
output = [1, 3, 3, 7]

The second loop would take the output of the first loop as its input array and write to old input array:
Stride = 2:
i = 0 --> (i + 1) % (2*2) = 1, so output[0] = 1 = input[0]
i = 1 --> (i + 1) % (2*2) = 2, so output[1] = 3 = input[1]
i = 2 --> (i + 1) % (2*2) = 3, so output[2] = 3 = input[2]
i = 3 --> (i + 1) % (2*2) = 0, so output[3] = 7 + 3 = input[3] + input[1]

input = [1, 3, 3, 7]
output = [1, 3, 3, 10]

Kernel B begins with the value that stride ends at (n/2), and decreases (by halving) until it reaches one. If the process id i satisfies ((i>0) && ((i+1) % (2*stride) == stride)) then it stores the result of the element at id `i` plus the element at id `(i-stride)` (from the input arrays) in the `i`th element of the output array. Otherwise, we take the ith

Continuing from the previous example:
The first loop of the broadcast kernel progresses as such:
Stride = 2:
i = 0 --> (i>0) and ((i+1) % (2*2) == 1), so output[0] = 1 = input[0]
i = 1 --> (i>0) and ((i+1) % (2*2) == 2), so output[1] = 3 = input[1] + input[-1]
i = 2 --> (i>0) and ((i+1) % (2*2) == 3), so output[2] = 3 = input[2]
i = 3 --> (i>0) and ((i+1) % (2*2) == 0), so output[3] = 10 = input[3]
input = [1, 3, 3, 10]
output = [1, 3, 3, 10]

And the second round:
Stride = 1:
i = 0 --> (i>0) and ((i+1) % (2*1) == 1), so output[0] = 1 = input[0]
i = 1 --> (i>0) and ((i+1) % (2*1) == 0), so output[1] = 3 = input[1] + input[-1]
i = 2 --> (i>0) and ((i+1) % (2*1) == 1), so output[2] = 3 + 3 = input[2] + input[2]
i = 3 --> (i>0) and ((i+1) % (2*1) == 0), so output[3] = 10 = input[3]
input = [1, 3, 3, 10]
output = [1, 3, 6, 10] // which is our desired result
