# Mini-Me MCP Server Lemmatization Improvements

## Overview
Enhance the mini-me MCP server's lemmatization capabilities by implementing frequency-based term sorting, limiting output to top terms, and improving word filtering based on the ChatGPT Export Processor's implementation.

## Current Implementation
Located at: `c:/dev/od-dm-y/OneDrive/dev-projects/mini-me/mini-me/src/index.ts`

### Dependencies
- natural: For word tokenization and stemming
- stopword: For removing common words

### Current Features
- Word tokenization using natural's WordTokenizer
- Basic stopword removal
- Porter Stemmer algorithm for word reduction
- Simple duplicate removal

## Reference Implementation
Located at: `C:/dev/od-dm-etp/OneDrive - Exact Technology Partners/Documents/~AI/Data Exports/ChatGPT-Export-Processor/chat_processor.py`

### Key Features to Adopt
1. NLTK's advanced word processing
2. Custom stopwords handling
3. Frequency-based term analysis
4. Bigram collocation detection

## Planned Improvements

### 1. Term Frequency Analysis
```typescript
interface TermFrequency {
  term: string;
  count: number;
  percentage: number;
}

function analyzeTermFrequency(terms: string[]): TermFrequency[] {
  const frequencies = new Map<string, number>();
  const totalTerms = terms.length;
  
  // Count occurrences
  terms.forEach(term => {
    frequencies.set(term, (frequencies.get(term) || 0) + 1);
  });
  
  // Convert to array and sort by frequency
  return Array.from(frequencies.entries())
    .map(([term, count]) => ({
      term,
      count,
      percentage: (count / totalTerms) * 100
    }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 20); // Limit to top 20
}
```

### 2. Enhanced Word Filtering
```typescript
const TRIVIAL_WORDS = new Set([
  // Common English articles
  'a', 'an', 'the',
  // Common prepositions
  'in', 'on', 'at', 'by', 'for', 'with', 'to',
  // Common conjunctions
  'and', 'or', 'but',
  // Common pronouns
  'i', 'you', 'he', 'she', 'it', 'we', 'they',
  // Common auxiliary verbs
  'is', 'are', 'was', 'were', 'be', 'been', 'being',
  'have', 'has', 'had', 'do', 'does', 'did',
  // Common adverbs
  'very', 'really', 'quite', 'just',
  // Programming-specific trivial words
  'function', 'var', 'let', 'const', 'return'
]);
```

### 3. Updated CodeAnalysisResult Interface
```typescript
interface CodeAnalysisResult {
  lineCount: number;
  complexity: number;
  suggestions: string[];
  lemmatizedTerms: {
    term: string;
    count: number;
    percentage: number;
  }[];
}
```

### 4. Improved Lemmatization Function
```typescript
async function analyzeLemmatizedTerms(text: string): Promise<TermFrequency[]> {
  // Remove punctuation and convert to lowercase
  const cleanText = text.toLowerCase().replace(/[^\w\s]/g, '');
  
  // Tokenize
  const tokens = tokenizer.tokenize(cleanText) || [];
  
  // Remove stopwords and trivial words
  const filteredTokens = tokens.filter(token => 
    !TRIVIAL_WORDS.has(token) && 
    !eng.includes(token)
  );
  
  // Stem tokens
  const stemmedTokens = filteredTokens.map(token => 
    PorterStemmer.stem(token)
  );
  
  // Analyze frequencies
  return analyzeTermFrequency(stemmedTokens);
}
```

## Implementation Steps

1. Update Dependencies
```json
{
  "dependencies": {
    "@modelcontextprotocol/sdk": "0.6.0",
    "natural": "^6.10.4",
    "stopword": "^2.0.8"
  }
}
```

2. Create Type Definitions
- Add TermFrequency interface
- Update CodeAnalysisResult interface
- Add type declarations for external modules

3. Implement Core Functions
- Term frequency analysis
- Enhanced word filtering
- Updated lemmatization with frequency counting

4. Update analyze_code Handler
- Modify to use new lemmatization function
- Include frequency information in output
- Limit output to top 20 terms

5. Testing
- Test with various file types
- Verify frequency counting
- Validate stopword filtering
- Check performance with large files

## File Structure
```
mini-me/
├── src/
│   ├── index.ts              # Main server file
│   ├── types/
│   │   └── stopword.d.ts     # Type declarations
│   └── utils/
│       └── lemmatizer.ts     # Lemmatization utilities
├── package.json
└── tsconfig.json
```

## Expected Output Format
```json
{
  "lineCount": 128,
  "complexity": 3430,
  "suggestions": [
    "Consider breaking this file into smaller modules",
    "Add more comments to improve code documentation"
  ],
  "lemmatizedTerms": [
    {
      "term": "function",
      "count": 15,
      "percentage": 8.5
    },
    {
      "term": "process",
      "count": 12,
      "percentage": 6.8
    }
  ]
}
```

## Notes
- Maintain backward compatibility with existing API
- Ensure proper error handling for large files
- Consider caching frequent terms for performance
- Document any new configuration options
- Add logging for debugging purposes

## References
1. ChatGPT Export Processor implementation
2. Natural.js documentation
3. MCP SDK documentation
4. TypeScript best practices