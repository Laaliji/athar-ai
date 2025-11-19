import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

const LearnMorePanel = () => {
  const [expandedFaq, setExpandedFaq] = useState(null);

  const educationalCards = [
    {
      id: 1,
      title: 'Science & Philosophy',
      description: 'Discover the groundbreaking advancements in astronomy, medicine, and mathematics during this era.',
      image: '/images/science-card.png',
    },
    {
      id: 2,
      title: 'Art & Architecture',
      description: 'Explore the breathtaking calligraphy, geometric patterns, and architectural marvels.',
      image: '/images/architecture-card.png',
    },
  ];

  const faqs = [
    {
      id: 1,
      question: 'What was the House of Wisdom?',
      answer: 'The House of Wisdom (Bayt al-Hikma) was a major intellectual center in Baghdad during the Islamic Golden Age, serving as a library, translation institute, and research center.',
    },
    {
      id: 2,
      question: 'When did the Golden Age of Islam occur?',
      answer: 'The Islamic Golden Age is generally considered to have lasted from the 8th to the 13th centuries, a period of remarkable scientific and cultural achievements.',
    },
    {
      id: 3,
      question: 'What are some major contributions from this period?',
      answer: 'Major contributions include advancements in algebra, algorithms, astronomy, medicine, optics, and the preservation of classical Greek and Roman knowledge.',
    },
  ];

  const toggleFaq = (id) => {
    setExpandedFaq(expandedFaq === id ? null : id);
  };

  return (
    <div className="h-full overflow-y-auto p-6" style={{ backgroundColor: 'var(--bg-primary)' }}>
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2 gradient-text">Learn More</h2>
        <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
          Explore the rich history and heritage of Islamic civilization
        </p>
      </div>

      {/* Educational Cards */}
      <div className="space-y-4 mb-8">
        {educationalCards.map((card) => (
          <div key={card.id} className="learn-card">
            <img src={card.image} alt={card.title} />
            <div className="learn-card-content">
              <h3 className="learn-card-title">{card.title}</h3>
              <p className="learn-card-description">{card.description}</p>
            </div>
          </div>
        ))}
      </div>

      {/* FAQ Section */}
      <div>
        <h3 className="text-lg font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>
          Frequently Asked Questions
        </h3>
        <div className="space-y-2">
          {faqs.map((faq) => (
            <div key={faq.id} className="faq-item">
              <div className="faq-question" onClick={() => toggleFaq(faq.id)}>
                <span>{faq.question}</span>
                {expandedFaq === faq.id ? (
                  <ChevronUp size={18} style={{ color: 'var(--accent-primary)' }} />
                ) : (
                  <ChevronDown size={18} style={{ color: 'var(--text-secondary)' }} />
                )}
              </div>
              {expandedFaq === faq.id && (
                <div className="faq-answer fade-in">
                  {faq.answer}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default LearnMorePanel;
