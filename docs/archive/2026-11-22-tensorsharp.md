# TensorSharp (C#/.NET engine on ggml) on Apple Silicon

> **Archived snapshot.** Kept as measured on that date; the current answer is in [runtimes](../findings/runtimes.md).

**Measured:** 2026-11-22. Built from source ([zhongkaifu/TensorSharp](https://github.com/zhongkaifu/TensorSharp)
main `5c97544`, .NET 10.0.404, CMake 4.5.1, `-p:TensorSharpSkipMlxNative=true`), served with
`TensorSharp.Server.Host --backend ggml_metal`. Its API requires the `model` field (the hosted model's id).

- **Inkling-2-Mini does not run on Mac with Unsloth's files.**
  - Root UD GGUFs: `KeyNotFoundException: blk.24.attn_rel_bias.weight`. TensorSharp reads `block_count` (48 virtual
    visits in Unsloth's looped layout) as physical layers (24).
  - `Mainline_Support/*.gguf_file` (`inkling2_loop` layout): loads, then `ggml_metal: unsupported op 'MUL_MAT_ID'`.
    The experts are NVFP4 in every Unsloth Inkling quant, and upstream ggml Metal has no NVFP4 MoE matmul yet.
- **Tiel-Coder-35B-A3B IQ4_XS + MTP (`--spec`, max draft 8):** stream decode **75–92 tok/s**, acceptance 64–65%
  (llama.cpp fork: 90–103 engine tok/s on the same file; TensorSharp returns no engine timings, so the counters
  differ). Thinking is off by default. Mini-eval 8/10, against 9/10 for llama.cpp with thinking off.
- **Prefix cache works:** a follow-up reused 3,680 of 3,725 prompt tokens and checkpoints persist on disk.
- **Verdict:** no speed gain over the Unsloth llama.cpp fork on this Mac. Worth re-checking for Inkling once ggml
  Metal gets NVFP4 `MUL_MAT_ID`.

Raw data: `results/*/*tensorsharp*`.
