# 🌙 Athar.AI — Modern Islamic Heritage Explorer

**Athar.AI** is a cutting-edge web platform for exploring Islamic civilization through AI-powered conversations. Built with modern FastAPI + React architecture and **100% free models** - no API keys required!

## ✨ Platform Features

- **🆓 Completely Free**: Uses open-source models (no OpenAI/API costs)
- **🌐 Modern Web Platform**: Beautiful React frontend with FastAPI backend
- **🧠 Advanced RAG System**: Smart retrieval with source citations
- **📚 Rich Dataset**: Curated Islamic heritage knowledge base
- **🎨 Islamic-Inspired Design**: Elegant UI with cultural aesthetics
- **⚡ Real-time Chat**: Instant responses with typing indicators
- **🔍 Source Transparency**: Every answer shows Wikipedia sources
- **📱 Responsive Design**: Works on desktop, tablet, and mobile

## 🏗️ Modern Architecture

- **Frontend**: React 18 + Tailwind CSS + Framer Motion + shadcn/ui
- **Backend**: FastAPI + Python with async support
- **UI Components**: Radix UI primitives with custom Islamic styling
- **Animations**: Advanced Framer Motion with spring physics
- **AI Models**: FLAN-T5, DialoGPT, DistilGPT2 (free)
- **Embeddings**: Multilingual sentence transformers
- **Vector DB**: ChromaDB with enhanced metadata
- **Framework**: LangChain with specialized prompts
- **Notifications**: React Hot Toast with custom styling

## 🚀 Quick Start

### Option 1: Enhanced Platform (Recommended)

```bash
# Setup enhanced platform with shadcn/ui
python setup_enhanced_platform.py

# Then launch the platform
python run_platform.py
```

Then visit: http://localhost:3000

### Option 2: Backend Only

```bash
cd backend
pip install -r requirements.txt
python main.py
```

API available at: http://localhost:8000

### Option 3: Legacy Interfaces

```bash
# Streamlit app
streamlit run streamlit_app.py

# CLI interface
python enhanced_free_rag.py

# Jupyter notebook
jupyter notebook enhanced_rag_notebook.ipynb
```

## 📋 Requirements

- Python 3.8+
- 4GB+ RAM (8GB recommended)
- Optional: GPU for faster processing

## 🎯 What You Can Ask

- **History**: "What was the House of Wisdom?"
- **Architecture**: "Describe Islamic architectural features"
- **Scholars**: "Who was Ibn Khaldun?"
- **Art**: "Tell me about Islamic calligraphy"
- **Sites**: "What makes the Alhambra special?"
- **Science**: "What innovations came from the Islamic Golden Age?"

## 🔧 Enhanced vs Original

| Feature   | Original         | Enhanced                          |
| --------- | ---------------- | --------------------------------- |
| LLM       | Requires API key | Free local models                 |
| Prompting | Basic            | Specialized for Islamic heritage  |
| Sources   | Limited          | Full citations with URLs          |
| Interface | Notebook only    | CLI + Web + Notebook              |
| Dataset   | Basic Wikipedia  | Expanded topics + metadata        |
| Setup     | Manual           | Automated with `setup_and_run.py` |

## ⚠️ Important Disclaimers

- **Educational Purpose**: Provides historical and cultural information only
- **No Religious Rulings**: Does not interpret religious texts or provide theological advice
- **Source-Based**: All answers are grounded in provided academic sources

## 🎨 Design & Theme

Athar.AI features a carefully crafted Islamic-inspired design:

- **Color Palette**: Deep blues, warm golds, and emerald greens
- **Typography**: Playfair Display for headings, Inter for body text
- **Patterns**: Subtle geometric Islamic patterns in backgrounds
- **Animations**: Smooth, respectful motion design
- **Accessibility**: RTL support ready for Arabic content

## 📱 Platform Screenshots

### Modern Chat Interface

- Real-time conversations with AI
- Source citations with Wikipedia links
- Typing indicators and smooth animations
- Mobile-responsive design

### Features Showcase

- Welcome screen with sample questions
- Sidebar with system information
- Loading states and error handling
- Islamic geometric pattern backgrounds

## 🛠️ Development Setup

### Prerequisites

- Python 3.8+
- Node.js 16+
- 4GB+ RAM (8GB recommended)
- Optional: GPU for faster AI processing

### Backend Development

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
cd frontend
npm install
npm start
```

### Full Stack Development

```bash
# Terminal 1: Backend
cd backend && python main.py

# Terminal 2: Frontend
cd frontend && npm start
```

## 🔧 Configuration

### Environment Variables

Create `.env` files for configuration:

**Backend (.env)**

```bash
# Optional: Customize model settings
RAG_MODEL_NAME=distilgpt2
CHUNK_SIZE=600
MAX_SOURCES=3
```

**Frontend (.env)**

```bash
REACT_APP_API_URL=http://localhost:8000
REACT_APP_VERSION=2.0.0
```

### Model Selection

Choose AI models based on your needs:

- **FLAN-T5**: Best accuracy, instruction-following
- **DialoGPT**: Conversational, natural responses
- **DistilGPT2**: Fastest, lightweight option

## 📊 Performance & Scaling

### Current Performance

- **Response Time**: < 2 seconds average
- **Accuracy**: Source-grounded responses
- **Cost**: $0.00 (completely free)
- **Concurrent Users**: 10+ (single instance)

### Scaling Options

- **Horizontal**: Multiple backend instances
- **GPU Acceleration**: 3-5x faster processing
- **Caching**: Redis for frequent queries
- **CDN**: Static asset optimization

## 🤝 Contributing

We welcome contributions to Athar.AI!

### Areas for Contribution

- **Dataset Expansion**: Add more Islamic heritage sources
- **UI/UX Improvements**: Enhance the user interface
- **Performance**: Optimize AI model performance
- **Localization**: Add Arabic language support
- **Documentation**: Improve guides and tutorials

### Development Workflow

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📄 License & Ethics

### License

This project is open-source under MIT License. See `LICENSE` file for details.

### Ethical Guidelines

- **Educational Purpose**: Designed for learning about Islamic heritage
- **Cultural Sensitivity**: Respectful representation of Islamic culture
- **No Religious Rulings**: Avoids theological interpretations
- **Source Attribution**: All content properly cited
- **Privacy**: No personal data collection

### Data Sources

- Wikipedia articles (CC BY-SA license)
- Public domain historical texts
- Academic papers (open access)
- Museum collections (public domain)

## 🔗 Links & Resources

- **Live Demo**: [athar-ai.com](https://athar-ai.com) (coming soon)
- **Documentation**: [docs.athar-ai.com](https://docs.athar-ai.com)
- **GitHub**: [github.com/your-repo/athar-ai](https://github.com/your-repo/athar-ai)
- **Issues**: Report bugs and request features
- **Discussions**: Community discussions and Q&A

## 🏆 Acknowledgments

- **LangChain**: For the RAG framework
- **Hugging Face**: For free AI models
- **Wikipedia**: For Islamic heritage content
- **React & FastAPI**: For modern web architecture
- **Islamic Art**: For design inspiration

---

**Built with ❤️ for exploring the rich heritage of Islamic civilization**

_"Seek knowledge from the cradle to the grave" - Islamic Proverb_
