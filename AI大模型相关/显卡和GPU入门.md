# 显卡基本结构
【【硬核科普】从零开始认识显卡】 https://www.bilibili.com/video/BV1xE421j7Uv/?share_source=copy_web&vd_source=8696b0300d8768b6657ac38806aa5330
![[attachments/Pasted image 20241210215615.png]]
- 显卡由电路板和散热模组组成
- 显卡电路板可认为由四个部分组成：GPU、显存、供电模块、接口
- 接口包括视频接口和PCIE接口
	- 视频接口：将运算好的图像发送给显示器
	- PCIE接口：和CPU、内存交互数据
- GPU
	- SM：流式多处理器，是包含多个处理器的单元
	- L2 Cache
	- NVENC视频编码器：把视频转换成新的格式或大小
	- NVDEC视频解码器：把数据流转换为视频画面
	- 显存控制器：控制GPU与显存交互
	- PCIE控制器：控制GPU与CPU、内存等主板上元器件交互
# 名词解释
### 处理器
- SM：流式多处理器，是包含多个处理器的单元
	- CUDA Core：CUDA核心，可视为简单的计算器，可计算整型和浮点数的乘法和加法
	- Tensor Core：张量核心，专注于矩阵的乘法和加法
	- RT Core：RAY Tracing 光追核心 
- SIMD：单指令多数据，同一指令可应用到多个不同的数据上
- SIMT：单指令多线程，可以理解为是SIMD的改进
- WARP：是NVIDIA GPU中用于执行SIMD/SIMT的基本调度单位。Warp可以被认为是一个执行单元，一般由32个线程组成，这些线程同时执行相同的指令，但操作不同的数据
- 线程块：

> 当一个核函数（kernel）在GPU上执行时，以下是执行流程：
>1. **线程块划分**：核函数的所有线程被划分成多个线程块（Thread Blocks）。
>2. **Warp划分**：每个线程块被进一步划分成多个Warp，每个Warp有32个线程。
>3. **调度和执行**： 每个Warp被分派到一个SM的Warp调度器上。Warp中的32个线程被分配到SM内的CUDA Core上执行。由于Warp中的线程执行相同的指令，所以多个CUDA Core可以同时并行执行这些线程。

### 显存
- HBM（High Bandwidth Memory）通过堆叠内存芯片（dies），在单个封装内实现多层内存堆叠，并使用宽的总线（通常为1024位）连接到GPU或CPU，从而提供极高的内存带宽。相比传统GDDR5/6显存，HBM能够提供数倍的带宽。
- 显卡制造商在选择HBM或GDDR显存时，会综合考虑性能需求、成本、功耗和市场定位等因素。HBM显存通常用于需要极高带宽和能效的专业计算和高端图形应用，而GDDR显存则在高性能游戏和主流市场中更为常见。
### 算力指标

衡量GPU算力的指标
FP32
- TFlops：Tera Floating Point Operations Per Second 的缩写，表示每秒万亿次浮点运算。