---
layout: default
---

# 使用llama.app转换模型文件后在ollama运行

https://huggingface.co/qihoo360/TinyR1-32B-Preview，这个模型很厉害的样子，运行起来看看怎么样。

使用ollama是运行大模型最简单的方法，[ollama下载](https://ollama.com/download)，那就用ollama运行这个模型，可是这个模型的文件是 .safetensors，怎么办？

要将 Hugging Face 上的 .safetensors 格式模型转换为 Ollama 支持的格式并运行，需要一些额外的步骤。Ollama 目前主要支持 GGUF 或 GGML 格式的模型，而 .safetensors 是 Hugging Face 的一种高效模型存储格式，因此需要进行格式转换

##### 第一步，下载模型文件

huggingface.co打不开没关系，国内有个镜像站 [huggingface镜像站](https://hf-mirror.com)

```
export HF_ENDPOINT=https://hf-mirror.com
huggingface-cli download qihoo360/TinyR1-32B-Preview --local-dir TinyR1-32B-Preview

Fetching 21 files: 100%|█████████████████████████████████████████████████████████████████████████| 21/21 [00:00<00:00, 7241.67it/s]
/data/tiny/TinyR1-32B-Preview
```

##### 第二步，安装llama.cpp

llama.cpp 可以把.safetensors文件转换为GGUF格式，ollama可以使用GGUF文件。下面编译可选，因为github上已经有编译好的，

llama-b4778-bin-ubuntu-vulkan-x64.zip   下载这个文件，ubuntu、centos8 都可以使用，免去下面编译

```
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp
make   # 直接make 如提示
Makefile:2: *** The Makefile build is deprecated. Use the CMake build instead. For more details, see https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md.  Stop.

mkdir build
cd build/
cmake ..
cmake --build . 
ls bin/
libggml-base.so                llama-gbnf-validator           llama-lookup-stats     llama-simple-chat         test-grammar-integration
libggml-cpu.so                 llama-gen-docs                 llama-minicpmv-cli     llama-speculative         test-grammar-parser
libggml.so                     llama-gguf                     llama-parallel         llama-speculative-simple  test-json-schema-to-grammar
libllama.so                    llama-gguf-hash                llama-passkey          llama-tokenize            test-llama-grammar
libllava_shared.so             llama-gguf-split               llama-perplexity       llama-tts                 test-log
llama-batched                  llama-gritlm                   llama-q8dot            llama-vdot                test-model-load-cancel
llama-batched-bench            llama-imatrix                  llama-quantize         test-arg-parser           test-quantize-fns
llama-bench                    llama-infill                   llama-quantize-stats   test-autorelease          test-quantize-perf
llama-cli                      llama-llava-cli                llama-qwen2vl-cli      test-backend-ops          test-rope
llama-convert-llama2c-to-ggml  llama-llava-clip-quantize-cli  llama-retrieval        test-barrier              test-sampling
llama-cvector-generator        llama-lookahead                llama-run              test-c                    test-tokenizer-0
llama-embedding                llama-lookup                   llama-save-load-state  test-chat                 test-tokenizer-1-bpe
llama-eval-callback            llama-lookup-create            llama-server           test-chat-template        test-tokenizer-1-spm
llama-export-lora              llama-lookup-merge             llama-simple           test-gguf
```

##### 第三步，使用llama转换大模型文件格式

先pip安装依赖,再转换文件，python3 convert_hf_to_gguf.py 大模型文件夹地址 --outfile 名称.gguf。safetensors文件有多个，当转换为gguf格式时，会自动合并为一个文件

```
cd llama.cpp
pip install -r requirements/requirements-convert_legacy_llama.txt
python3 convert_hf_to_gguf.py ../TinyR1-32B-Preview/ --outfile TinyR1-32B-Preview.gguf

torch.bfloat16 --> F16   # 转换为 F16精度
torch.bfloat16 --> F32
INFO:hf-to-gguf:Set model quantization version
INFO:gguf.gguf_writer:Writing the following files:
INFO:gguf.gguf_writer:TinyR1-32B-Preview.gguf: n_tensors = 771, total_size = 65.5G
Writing: 100%|██████████████████████████████████████████████████████████████████████████████████████| 65.5G/65.5G [09:21<00:00, 117Mbyte/s]
INFO:hf-to-gguf:Model successfully exported to TinyR1-32B-Preview.gguf
```

##### 第四步 使用ollama运行

需要先创建个Modelfile，像Dockerfile一样，加入引用文件地址

```
# cat Modelfile 
FROM /data/llama.cpp/TinyR1-32B-Preview.gguf
# ollama create TinyR1-32B-Preview -f Modelfile
# ollama list 
NAME                         ID              SIZE      MODIFIED      
TinyR1-32B-Preview:latest    0dec908815dc    65 GB     8 seconds ago 
# ollama ps
NAME                         ID              SIZE     PROCESSOR          UNTIL              
TinyR1-32B-Preview:latest    0dec908815dc    70 GB    33%/67% CPU/GPU    4 minutes from now  
```

##### 第五步 模型量化为int8

运行起来比较费劲，单独的GPU撑不住，CPU已经调度了，将模型量化为int8

量化可以减小内存大小，减小模型体积，不过模型精度也会低一些

```
# ollama rm TinyR1-32B-Preview:latest
deleted 'TinyR1-32B-Preview:latest'
# /data/llama.cpp/build/bin/llama-quantize TinyR1-32B-Preview.gguf  # 查看可选的量化
# /data/llama.cpp/build/bin/llama-quantize TinyR1-32B-Preview.gguf TinyR1-32B-Preview-8b.gguf Q8_0
# ll -h
-rw-r--r--  1 root root  33G Feb 25 15:05 TinyR1-32B-Preview-8b.gguf
-rw-r--r--  1 root root  62G Feb 25 12:30 TinyR1-32B-Preview.gguf
```


2025年2月26日 于 [linux工匠](https://bbotte.github.io/) 发表