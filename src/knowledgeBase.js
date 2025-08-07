// Knowledge Base for b.om Institute Chat Widget
const knowledgeBase = {
  greetings: {
    patterns: ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'greetings'],
    responses: [
      'Welcome to b.om Institute. How can I help you today?',
      'Hello! How can I assist you with b.om Institute today?',
      'Welcome! How may I help you with b.om Institute?'
    ]
  },
  about: {
    patterns: ['what is b.om', 'about b.om', 'tell me about b.om', 'who are you'],
    responses: [
      'b.om Institute is a premier institution focused on technology and innovation education, offering cutting-edge programs and research opportunities.',
      'We are a leading educational institution dedicated to excellence in technology, design, and innovation.'
    ]
  },
  programs: {
    patterns: ['programs', 'degrees', 'courses', 'what do you offer', 'academics'],
    responses: [
      'We offer various programs including:\n• B.Sc. in Computer Science\n• M.Sc. in Data Science\n• Professional Certificates\n\nWhich program interests you?',
      'Our programs cover:\n• Software Engineering\n• Cybersecurity\n• AI & Machine Learning\n• UX/UI Design\n\nNeed details on any specific program?'
    ]
  },
  admission: {
    patterns: ['admission', 'how to apply', 'requirements', 'deadlines', 'enroll'],
    responses: [
      'Our admission process includes:\n1. Online application\n2. Academic transcripts\n3. Letters of recommendation\n4. Statement of purpose\n\nWould you like more details?',
      'To apply, visit our website or contact admissions for assistance with the application process.'
    ]
  },
  contact: {
    patterns: ['contact', 'email', 'phone', 'address', 'location', 'how to reach'],
    responses: [
      'You can reach us at:\n📧 info@bominstitute.edu\n📞 +1 (555) 987-6543\n📍 123 Innovation Drive, Tech Valley',
      'Contact our team at admissions@bominstitute.edu or call +1 (555) 987-6543 for assistance.'
    ]
  },
  default: {
    responses: [
      'I\'m here to help! Could you provide more details about your question?',
      'I want to make sure I understand. Could you rephrase your question?',
      'I\'d be happy to help with that. Could you provide more context?'
    ]
  }
};

// Function to find a response based on user input
export function getResponse(userInput) {
  const input = userInput.toLowerCase();
  
  // Check each category for matching patterns
  for (const [category, data] of Object.entries(knowledgeBase)) {
    if (category === 'default') continue;
    
    const hasMatch = data.patterns.some(pattern => 
      input.includes(pattern.toLowerCase())
    );
    
    if (hasMatch) {
      const responses = data.responses;
      return responses[Math.floor(Math.random() * responses.length)];
    }
  }
  
  // Return a default response if no match found
  const defaultResponses = knowledgeBase.default.responses;
  return defaultResponses[Math.floor(Math.random() * defaultResponses.length)];
}
