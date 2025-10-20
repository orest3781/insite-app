# Recommended Ollama Models

**Last Updated:** October 12, 2025  
**For:** InSite App - Previewless Insight Viewer

---

## Pre-Configured Models in Settings

The settings dialog now includes a dropdown with the **best available Ollama models** pre-configured:

### 🏆 Recommended Models (in order)

#### 1. **llama3.2** ⭐ (Default)
- **Best for:** General-purpose tasks, balanced performance
- **Size:** ~2GB (3B parameters)
- **Speed:** Fast
- **Accuracy:** Excellent
- **Use case:** Default choice for most users
- **Install:** `ollama pull llama3.2`

#### 2. **llama3.2:1b**
- **Best for:** Lightweight, resource-constrained systems
- **Size:** ~1GB (1B parameters)
- **Speed:** Very fast
- **Accuracy:** Good
- **Use case:** Low-end hardware, quick processing
- **Install:** `ollama pull llama3.2:1b`

#### 3. **llama3.1**
- **Best for:** Previous stable version
- **Size:** ~4.7GB (8B parameters)
- **Speed:** Moderate
- **Accuracy:** Excellent
- **Use case:** Fallback if 3.2 has issues
- **Install:** `ollama pull llama3.1`

#### 4. **qwen2.5** ⭐
- **Best for:** Multilingual, excellent reasoning
- **Size:** ~4.7GB (7B parameters)
- **Speed:** Fast
- **Accuracy:** Excellent
- **Use case:** Alternative to Llama, great for non-English
- **Install:** `ollama pull qwen2.5`

#### 5. **qwen2.5:7b**
- **Best for:** Balanced Qwen version
- **Size:** ~4.7GB
- **Speed:** Fast
- **Accuracy:** Excellent
- **Use case:** Explicit 7B variant
- **Install:** `ollama pull qwen2.5:7b`

#### 6. **gemma2**
- **Best for:** Google's latest, efficient
- **Size:** ~5.4GB (9B parameters)
- **Speed:** Moderate
- **Accuracy:** Excellent
- **Use case:** Alternative to Llama/Qwen
- **Install:** `ollama pull gemma2`

#### 7. **mistral**
- **Best for:** Balanced performance
- **Size:** ~4.1GB (7B parameters)
- **Speed:** Fast
- **Accuracy:** Very good
- **Use case:** Solid alternative choice
- **Install:** `ollama pull mistral`

#### 8. **mistral-nemo**
- **Best for:** Larger context, better reasoning
- **Size:** ~7GB (12B parameters)
- **Speed:** Moderate
- **Accuracy:** Excellent
- **Use case:** Complex documents
- **Install:** `ollama pull mistral-nemo`

#### 9. **phi3**
- **Best for:** Microsoft's efficient model
- **Size:** ~2.3GB (3.8B parameters)
- **Speed:** Fast
- **Accuracy:** Very good
- **Use case:** Windows users, efficiency
- **Install:** `ollama pull phi3`

#### 10. **codellama**
- **Best for:** Code-heavy documents
- **Size:** ~3.8GB (7B parameters)
- **Speed:** Fast
- **Accuracy:** Good (code-focused)
- **Use case:** Technical documentation, source code
- **Install:** `ollama pull codellama`

#### 11. **deepseek-coder-v2**
- **Best for:** Advanced coding tasks
- **Size:** ~8.9GB (16B parameters)
- **Speed:** Slower
- **Accuracy:** Excellent for code
- **Use case:** Programming documentation, technical files
- **Install:** `ollama pull deepseek-coder-v2`

#### 12. **llama2**
- **Best for:** Legacy compatibility
- **Size:** ~3.8GB (7B parameters)
- **Speed:** Moderate
- **Accuracy:** Good
- **Use case:** Fallback, older systems
- **Install:** `ollama pull llama2`

---

## Quick Install Guide

### Install Default Model (Recommended)
```powershell
ollama pull llama3.2
```

### Install All Recommended Models
```powershell
# Core recommendations (install these first)
ollama pull llama3.2        # Default
ollama pull qwen2.5          # Alternative general-purpose
ollama pull mistral          # Balanced option

# Lightweight option
ollama pull llama3.2:1b      # For low-end systems

# Specialized options
ollama pull codellama        # For code-heavy documents
ollama pull phi3             # Microsoft efficient model
```

---

## Model Selection Guide

### Choose Based On:

#### Hardware
- **Low-end (4-8GB RAM):** llama3.2:1b, phi3
- **Mid-range (8-16GB RAM):** llama3.2, qwen2.5, mistral
- **High-end (16GB+ RAM):** llama3.1, gemma2, mistral-nemo, deepseek-coder-v2

#### Document Type
- **General documents:** llama3.2, qwen2.5
- **Code/Technical:** codellama, deepseek-coder-v2, phi3
- **Multilingual:** qwen2.5
- **Long documents:** mistral-nemo, llama3.1

#### Speed vs. Accuracy
- **Speed priority:** llama3.2:1b, phi3, mistral
- **Balanced:** llama3.2, qwen2.5:7b
- **Accuracy priority:** llama3.1, gemma2, mistral-nemo

---

## Performance Comparison

| Model | Size | Speed | Accuracy | Memory | Best For |
|-------|------|-------|----------|--------|----------|
| llama3.2 ⭐ | 2GB | Fast | Excellent | 4-8GB | Default choice |
| llama3.2:1b | 1GB | Very Fast | Good | 2-4GB | Low-end systems |
| llama3.1 | 4.7GB | Moderate | Excellent | 8-16GB | High accuracy |
| qwen2.5 ⭐ | 4.7GB | Fast | Excellent | 8-16GB | Multilingual |
| gemma2 | 5.4GB | Moderate | Excellent | 8-16GB | Alternative |
| mistral | 4.1GB | Fast | Very Good | 6-12GB | Balanced |
| mistral-nemo | 7GB | Moderate | Excellent | 12-24GB | Complex docs |
| phi3 | 2.3GB | Fast | Very Good | 4-8GB | Efficient |
| codellama | 3.8GB | Fast | Good | 6-12GB | Code-heavy |
| deepseek-coder-v2 | 8.9GB | Slower | Excellent | 16-32GB | Advanced code |
| llama2 | 3.8GB | Moderate | Good | 6-12GB | Legacy |

---

## Model Features in InSite App

### What the LLM Does
1. **Tag Generation:** Creates 6 descriptive tags per document
2. **Description Generation:** Writes 2-sentence summaries
3. **Classification:** Categorizes document type and content

### Optimal Settings
```json
{
  "ollama": {
    "host": "http://localhost:11434",
    "default_model": "llama3.2",
    "temperature": 0.4,
    "max_tokens": 270,
    "top_p": 0.7,
    "timeout_s": 30
  }
}
```

### Why These Settings?
- **Temperature 0.4:** Balanced creativity/consistency
- **Max tokens 270:** Enough for 6 tags + 2 sentences
- **Top_p 0.7:** Good diversity without randomness

---

## Troubleshooting

### Model Not Found
```powershell
# Install the model
ollama pull llama3.2

# Verify installation
ollama list
```

### Slow Performance
- Switch to lighter model (llama3.2:1b or phi3)
- Reduce max_tokens
- Close other applications

### Poor Quality Results
- Switch to larger model (llama3.1 or qwen2.5)
- Increase temperature slightly (0.5-0.6)
- Ensure OCR quality is good (LLM depends on input)

### Out of Memory
- Use smaller model (llama3.2:1b)
- Restart Ollama service
- Close other applications

---

## Custom Models

The dropdown is **editable**, so you can:
1. Type any custom model name
2. Use specific versions (e.g., `llama3.2:latest`)
3. Use custom fine-tuned models

---

## Version Information

**Model versions as of October 2025:**
- Llama 3.2 (latest)
- Qwen 2.5 (latest)
- Gemma 2 (latest)
- Mistral (latest stable)
- Phi-3 (latest)

**Check for updates:**
```powershell
ollama list
ollama pull <model-name>
```

---

## Recommendations Summary

### Best Overall: **llama3.2** ⭐
- Great balance of speed, accuracy, and resource usage
- Well-tested and stable
- Excellent for general document processing

### Best Alternative: **qwen2.5** ⭐
- Excellent for multilingual documents
- Great reasoning capabilities
- Comparable performance to llama3.2

### Best for Low-End Systems: **llama3.2:1b**
- Smallest footprint
- Still produces good results
- Fast processing

### Best for Code: **deepseek-coder-v2**
- Specialized for programming
- Excellent technical understanding
- Large but very capable

---

**All models are now pre-configured in the settings dropdown!**

Just select from the dropdown, or type a custom model name. The app will remember your choice.

**Default:** llama3.2 (already selected)
