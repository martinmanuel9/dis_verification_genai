# Model Selection Guide

Choose the right AI model for your needs.

## Quick Recommendations

**Best Overall**: `gpt-4o` (OpenAI)
- Highest quality
- Best for complex analysis
- Requires API key
- Cost: ~$0.005-0.015 per 1K tokens

**Best Local**: `llama3.1:8b` (Ollama)
- Good quality
- Runs on your hardware
- Privacy-focused
- Free to use

**Fastest**: `gpt-4o-mini` (OpenAI)
- Quick responses
- Cost-effective
- Good for simple tasks
- Cost: ~$0.0001-0.0006 per 1K tokens

**Most Private**: Any Ollama model
- All processing local
- No data leaves your infrastructure
- US-based model providers only

## OpenAI Models

### GPT-5 Series (Latest)

**gpt-5.1** - Cutting Edge
- Latest and most advanced
- Best reasoning capabilities
- Highest cost
- Use for: Complex analysis, critical decisions

**gpt-5** - Premium
- Excellent all-around performance
- Improved over GPT-4
- Use for: Important test plan generation

**gpt-5-mini** - Balanced
- Good quality, faster than gpt-5
- More affordable
- Use for: Standard document analysis

**gpt-5-nano** - Fast
- Optimized for speed
- Lower cost
- Use for: Quick analysis, chat

### GPT-4 Series (Proven)

**gpt-4o** - **RECOMMENDED**
- Best balance of quality/speed/cost
- Multimodal (handles images)
- Excellent for test plan generation
- **Use this for most tasks**

**gpt-4o-mini** - Cost-Effective
- 60% cheaper than gpt-4o
- Still very good quality
- Fast responses
- Use for: Chat, simple analysis

**gpt-4-turbo** - Legacy Premium
- Good quality but slower
- Being superseded by gpt-4o
- Use for: Compatibility

### Reasoning Models

**o1, o1-mini, o3-mini** - Specialized
- Designed for deep reasoning
- Slower but more thorough
- Use for: Complex problem-solving
- Not ideal for: Document extraction

### GPT-3.5

**gpt-3.5-turbo** - Legacy
- Older model
- Much cheaper
- Lower quality
- Use for: Basic tasks only

## Ollama Models (Local)

### Meta (California) - Llama Series

**llama3.1:8b** - **RECOMMENDED LOCAL**
- 8 billion parameters
- Excellent quality for local model
- Requires: 8 GB RAM minimum
- Good for: All tasks, on-premises deployment

**llama3.2:3b** - Compact
- 3 billion parameters
- Faster, less memory
- Requires: 4 GB RAM
- Good for: Resource-constrained systems

**llama3.2:1b** - Tiny
- 1 billion parameters
- Very fast
- Requires: 2 GB RAM
- Good for: Quick tasks, testing

### Microsoft (Washington)

**phi3:mini** - Efficient
- 3.8 billion parameters
- Optimized for efficiency
- Requires: 4 GB RAM
- Good for: Balanced local option

### Snowflake (Montana)

**snowflake-arctic-embed** - Embeddings
- Not for chat
- Used internally for RAG
- Generates vector embeddings

## Model Comparison

### Quality

```
Highest Quality
   ↓
gpt-5.1
gpt-5
gpt-4o
gpt-5-mini
gpt-4o-mini
llama3.1:8b
phi3:mini
llama3.2:3b
gpt-3.5-turbo
llama3.2:1b
   ↓
Lowest Quality
```

### Speed

```
Fastest
   ↓
gpt-5-nano
gpt-4o-mini
llama3.2:1b
phi3:mini
llama3.2:3b
gpt-4o
llama3.1:8b
gpt-5-mini
gpt-5
gpt-5.1
   ↓
Slowest
```

### Cost (OpenAI only)

```
Most Expensive
   ↓
gpt-5.1
gpt-5
o1
gpt-4o
gpt-5-mini
gpt-4o-mini
gpt-3.5-turbo
   ↓
Least Expensive

Ollama models: FREE (use your hardware)
```

### Privacy

```
Most Private (all equal)
   ↓
llama3.1:8b    ┐
llama3.2:3b    ├─ All processing local
llama3.2:1b    │  No data leaves infrastructure
phi3:mini      ┘
   ↓
Least Private (all equal)
   ↓
gpt-5.1        ┐
gpt-5          │
gpt-4o         ├─ Data sent to OpenAI
gpt-4o-mini    │  (see OpenAI privacy policy)
gpt-3.5-turbo  ┘
```

## Use Case Recommendations

### Test Plan Generation

**Best**: `gpt-4o`
- High quality extraction
- Good reasoning for test cases
- Handles complex documents

**Budget**: `gpt-4o-mini`
- Good quality
- Much cheaper
- Acceptable for most documents

**Local**: `llama3.1:8b`
- Best local option
- Good quality
- No API costs

### Interactive Chat

**Best**: `gpt-4o`
- Natural conversation
- Good context retention
- Fast enough

**Fast**: `gpt-4o-mini` or `gpt-5-nano`
- Quick responses
- Lower cost
- Good for rapid Q&A

**Local**: `llama3.1:8b` or `phi3:mini`
- Decent conversation quality
- Local privacy

### RAG (Document Q&A)

**Best**: `gpt-4o`
- Excellent at understanding context
- Good citation generation

**Budget**: `gpt-4o-mini`
- Very good for RAG
- Cost-effective
- Fast

**Local**: `llama3.1:8b`
- Good context understanding
- Acceptable citation quality

### Requirements Extraction

**Best**: `gpt-4o` with temperature 0.2
- Most accurate
- Deterministic
- Reliable

**Good**: `gpt-5-mini`
- Fast
- Good accuracy
- More affordable

**Local**: `llama3.1:8b` with temperature 0.1
- Acceptable accuracy
- Fully local

### Creative Test Scenarios

**Best**: `gpt-4o` with temperature 0.7-0.8
- Creative test ideas
- Good edge case identification

**Alternative**: `gpt-5`
- Very creative
- Novel approaches

## Hardware Requirements

### OpenAI Models
- No local hardware needed
- Runs in cloud
- Requires: Internet connection, API key

### Ollama Models

**llama3.1:8b**:
- CPU: 4+ cores
- RAM: 8 GB minimum (16 GB recommended)
- GPU: Optional (NVIDIA 8GB+ VRAM for 10x speedup)

**llama3.2:3b**:
- CPU: 2+ cores
- RAM: 4 GB minimum (8 GB recommended)
- GPU: Optional (NVIDIA 4GB+ VRAM)

**llama3.2:1b**:
- CPU: 2+ cores
- RAM: 2 GB minimum (4 GB recommended)
- GPU: Optional

**phi3:mini**:
- CPU: 2+ cores
- RAM: 4 GB minimum (8 GB recommended)
- GPU: Optional

**With GPU** (Linux only):
- 10-20x faster inference
- Lower RAM requirements
- NVIDIA GPU with CUDA support
- See: [Installation Guide](02-installation-setup.md#gpu-acceleration)

## Cost Analysis

### OpenAI Pricing (approximate)

**Test Plan Generation** (50-page document):
- gpt-5.1: ~$2.00
- gpt-5: ~$1.50
- gpt-4o: ~$0.50
- gpt-4o-mini: ~$0.15

**Chat Session** (30 messages):
- gpt-4o: ~$0.15
- gpt-4o-mini: ~$0.03

**RAG Query** (per question):
- gpt-4o: ~$0.01
- gpt-4o-mini: ~$0.002

### Ollama Costs

**All Ollama models**: FREE
- One-time download (1-8 GB per model)
- Uses your electricity/hardware
- No ongoing costs

**ROI Calculation**:
```
Typical usage: 100 test plans/month

OpenAI (gpt-4o): $50/month
Ollama (llama3.1:8b): $0/month + hardware

Break-even: 1-2 months if hardware available
```

## Switching Models

### Mid-Conversation

You can switch models anytime:

1. Select new model from dropdown
2. Next message uses new model
3. Previous messages preserved
4. Context maintained

**Use Case**: Start with fast model, switch to better model for complex questions

### Per-Agent

In Agent Manager, each agent can use different model:

```
Agent 1: gpt-4o (high quality extraction)
Agent 2: gpt-4o-mini (fast test generation)
Agent 3: llama3.1:8b (local validation)
```

## Model Selection Flowchart

```
Need test plan generation?
├─ Yes → Need best quality?
│        ├─ Yes → gpt-4o
│        └─ No → Budget priority?
│                ├─ Yes → gpt-4o-mini
│                └─ No → Privacy priority?
│                        ├─ Yes → llama3.1:8b
│                        └─ No → gpt-4o-mini
│
└─ No → Just chatting?
        ├─ Need fast responses?
        │   ├─ Yes → gpt-4o-mini or gpt-5-nano
        │   └─ No → gpt-4o
        └─ Local/private required?
            └─ Yes → llama3.1:8b or phi3:mini
```

## Compliance & Security

### US-Based Providers Only

**OpenAI**: Headquarters in San Francisco, CA
- Cloud-based (data processed in US)
- SOC 2 Type II certified
- See: https://openai.com/security

**Meta (Llama)**: Headquarters in Menlo Park, CA
- Local processing only
- No data transmission

**Microsoft (Phi)**: Headquarters in Redmond, WA
- Local processing only
- No data transmission

**Snowflake (Arctic Embed)**: Headquarters in Bozeman, MT
- Local processing only
- No data transmission

### Data Privacy

**OpenAI Models**:
- Data sent to OpenAI API
- See OpenAI's data usage policy
- Option to opt out of training
- API data not used for training by default

**Ollama Models**:
- All processing on your hardware
- No data leaves your infrastructure
- Suitable for classified/sensitive documents
- Air-gap capable

## Best Practices

### For Production

- **Primary**: `gpt-4o` for quality
- **Fallback**: `llama3.1:8b` if API unavailable
- **Cost Control**: Set monthly budget alerts
- **Monitoring**: Track model performance

### For Development

- **Testing**: `gpt-4o-mini` or `llama3.2:3b`
- **Debugging**: Same model as production
- **Experimentation**: Try different models

### For Compliance/Sensitive

- **Use Ollama models exclusively**
- **Deploy on-premises**
- **No internet required**
- **Full data control**

## Next Steps

- **[Getting Started](01-getting-started.md)** - Try different models
- **[Direct Chat](04-direct-chat.md)** - Compare model responses
- **[Document Generator](06-document-generator.md)** - Test models on real documents

---

Questions? See [FAQ](13-faq.md)
