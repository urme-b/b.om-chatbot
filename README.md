# b.om Institute Chat Widget

A compact, modern chat widget for b.om Institute's website. This React-based component provides an interactive chat interface that can be easily embedded into any webpage.

## Features

- **Compact Design**: Small chat icon that expands to a chat window
- **Modern UI**: Clean, professional look with Material-UI components
- **Responsive**: Works on all screen sizes
- **Easy to Customize**: Simple configuration for colors and messages

## Getting Started

### Prerequisites

- Node.js (v14 or later)
- npm (v6 or later)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/bom-chat-widget.git
   cd bom-chat-widget
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

4. Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

## Customization

### Knowledge Base
Edit `src/knowledgeBase.js` to update the bot's responses and patterns.

### Styling
Customize the theme and colors in `src/App.js` by modifying the theme configuration.

## Deployment

To create a production build:

```bash
npm run build
```

This will create a `build` directory with the optimized production build of your app.

## Embedding in a Website

1. Build the project:
   ```bash
   npm run build
   ```

2. Copy the contents of the `build` directory to your web server.

3. Add this script to your HTML:
   ```html
   <div id="root"></div>
   <script src="path/to/static/js/main.[hash].js"></script>
   ```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
