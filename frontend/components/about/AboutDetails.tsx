import React from "react";

export default function AboutPage() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          About RAG Studio
        </h1>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto">
          Your comprehensive platform for exploring, learning, and mastering
          Retrieval-Augmented Generation (RAG) techniques
        </p>
      </div>

      <div className="space-y-8">
        {/* Mission Section */}
        <div className="bg-white shadow-sm rounded-lg p-8">
          <h2 className="text-2xl font-semibold text-gray-900 mb-4">
            Our Mission
          </h2>
          <p className="text-gray-700 text-lg leading-relaxed mb-4">
            RAG Studio was born from a passion for making Retrieval-Augmented
            Generation accessible to everyone. Inspired by the vibrant{" "}
            <strong>Dynamous community</strong>, our goal is to demystify RAG by
            providing visual, interactive experiences that help you understand
            each step of the process.
          </p>
          <p className="text-gray-700 leading-relaxed">
            We believe learning should be fun, not frustrating. That&apos;s why
            RAG Studio offers hands-on exploration where you can experiment with
            different techniques, adjust settings to see real-time effects, and
            gain deep insights into how RAG systems work under the hood.
          </p>
        </div>

        {/* What is RAG Section */}
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-8">
          <h2 className="text-2xl font-semibold text-gray-900 mb-4">
            What is RAG?
          </h2>
          <p className="text-gray-700 leading-relaxed mb-4">
            <a
              href="https://blogs.nvidia.com/blog/what-is-retrieval-augmented-generation/"
              className="text-blue-600 hover:text-blue-800 underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              Retrieval-Augmented Generation (RAG)
            </a>{" "}
            is a technique that enhances AI models by connecting them to
            external knowledge sources. Instead of relying solely on training
            data, RAG systems can fetch relevant information from databases,
            documents, or other sources to provide more accurate and up-to-date
            responses.
          </p>
          <p className="text-gray-700 leading-relaxed">
            Think of it as giving your AI assistant access to a vast library -
            it can look up current information and cite sources, making
            responses more reliable and trustworthy.
          </p>
        </div>

        {/* What We Offer */}
        <div className="bg-white shadow-sm rounded-lg p-8">
          <h2 className="text-2xl font-semibold text-gray-900 mb-6">
            What RAG Studio Offers
          </h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div className="flex items-start">
                <div className="flex-shrink-0 w-2 h-2 bg-blue-500 rounded-full mt-2 mr-3"></div>
                <div>
                  <h3 className="font-medium text-gray-900">
                    Interactive RAG Exploration
                  </h3>
                  <p className="text-gray-600 text-sm">
                    Visual step-by-step breakdowns of RAG processes
                  </p>
                </div>
              </div>
              <div className="flex items-start">
                <div className="flex-shrink-0 w-2 h-2 bg-green-500 rounded-full mt-2 mr-3"></div>
                <div>
                  <h3 className="font-medium text-gray-900">
                    Multiple RAG Techniques
                  </h3>
                  <p className="text-gray-600 text-sm">
                    Compare different approaches and see their effects
                  </p>
                </div>
              </div>
              <div className="flex items-start">
                <div className="flex-shrink-0 w-2 h-2 bg-purple-500 rounded-full mt-2 mr-3"></div>
                <div>
                  <h3 className="font-medium text-gray-900">
                    Chatbot Playground
                  </h3>
                  <p className="text-gray-600 text-sm">
                    Test various chatbots powered by different RAG
                    implementations
                  </p>
                </div>
              </div>
            </div>
            <div className="space-y-4">
              <div className="flex items-start">
                <div className="flex-shrink-0 w-2 h-2 bg-yellow-500 rounded-full mt-2 mr-3"></div>
                <div>
                  <h3 className="font-medium text-gray-900">
                    Comprehensive Documentation
                  </h3>
                  <p className="text-gray-600 text-sm">
                    Curated library of RAG techniques and best practices
                  </p>
                </div>
              </div>
              <div className="flex items-start">
                <div className="flex-shrink-0 w-2 h-2 bg-red-500 rounded-full mt-2 mr-3"></div>
                <div>
                  <h3 className="font-medium text-gray-900">
                    Community Sharing
                  </h3>
                  <p className="text-gray-600 text-sm">
                    Share experiences and learn from other RAG enthusiasts
                  </p>
                </div>
              </div>
              <div className="flex items-start">
                <div className="flex-shrink-0 w-2 h-2 bg-indigo-500 rounded-full mt-2 mr-3"></div>
                <div>
                  <h3 className="font-medium text-gray-900">
                    Hands-On Learning
                  </h3>
                  <p className="text-gray-600 text-sm">
                    Experiment with your own models and data sources
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Current Capabilities */}
        <div className="bg-white shadow-sm rounded-lg p-8">
          <h2 className="text-2xl font-semibold text-gray-900 mb-6">
            Current Platform Capabilities
          </h2>

          {/* Data Sources */}
          <div className="mb-8">
            <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
              <svg
                className="w-5 h-5 text-blue-500 mr-2"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z" />
              </svg>
              Data Sources
            </h3>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="border border-gray-200 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-2">
                  Available Now
                </h4>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li>
                    •{" "}
                    <a
                      href="https://drive.google.com"
                      className="text-blue-600 hover:text-blue-800"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      Google Drive
                    </a>{" "}
                    integration
                  </li>
                  <li>• Local file upload (single source of truth)</li>
                </ul>
              </div>
              <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                <h4 className="font-medium text-gray-900 mb-2">Coming Soon</h4>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li>
                    •{" "}
                    <a
                      href="https://aws.amazon.com/s3/"
                      className="text-blue-600 hover:text-blue-800"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      Amazon S3
                    </a>{" "}
                    integration
                  </li>
                  <li>• Additional cloud storage providers</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Vector Databases */}
          <div className="mb-8">
            <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
              <svg
                className="w-5 h-5 text-green-500 mr-2"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M3 3a1 1 0 000 2v8a2 2 0 002 2h2.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L12.414 15H15a2 2 0 002-2V5a1 1 0 100-2H3zm11.707 4.707a1 1 0 00-1.414-1.414L10 9.586 8.707 8.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
              Vector Databases
            </h3>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="border border-gray-200 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-2">
                  Available Now
                </h4>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li>
                    •{" "}
                    <a
                      href="https://supabase.com/vector"
                      className="text-blue-600 hover:text-blue-800"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      Supabase
                    </a>{" "}
                    with pgvector search capabilities
                  </li>
                  <li>• PostgreSQL integration</li>
                </ul>
              </div>
              <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                <h4 className="font-medium text-gray-900 mb-2">Coming Soon</h4>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li>
                    •{" "}
                    <a
                      href="https://www.mongodb.com/products/platform/atlas-vector-search"
                      className="text-blue-600 hover:text-blue-800"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      MongoDB Atlas
                    </a>{" "}
                    vector search
                  </li>
                  <li>
                    •{" "}
                    <a
                      href="https://www.pinecone.io/"
                      className="text-blue-600 hover:text-blue-800"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      Pinecone
                    </a>{" "}
                    vector database
                  </li>
                  <li>
                    •{" "}
                    <a
                      href="https://neon.com/"
                      className="text-blue-600 hover:text-blue-800"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      NeonDB
                    </a>{" "}
                    serverless Postgres
                  </li>
                </ul>
              </div>
            </div>
          </div>

          {/* AI Models */}
          <div className="mb-8">
            <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
              <svg
                className="w-5 h-5 text-purple-500 mr-2"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z"
                  clipRule="evenodd"
                />
              </svg>
              AI Models
            </h3>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="border border-gray-200 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-2">
                  Available Now
                </h4>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li>
                    •{" "}
                    <a
                      href="https://platform.openai.com/docs/models"
                      className="text-blue-600 hover:text-blue-800"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      OpenAI GPT models
                    </a>{" "}
                    (GPT-4, GPT-3.5)
                  </li>
                  <li>• Built-in embedding generation</li>
                </ul>
              </div>
              <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                <h4 className="font-medium text-gray-900 mb-2">Coming Soon</h4>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li>• Bring your own API key support</li>
                  <li>• Multiple AI provider integration</li>
                  <li>• Custom model fine-tuning options</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Advanced RAG */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
              <svg
                className="w-5 h-5 text-red-500 mr-2"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M12.316 3.051a1 1 0 01.633 1.265l-4 12a1 1 0 11-1.898-.632l4-12a1 1 0 011.265-.633zM5.707 6.293a1 1 0 010 1.414L3.414 10l2.293 2.293a1 1 0 11-1.414 1.414l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0zm8.586 0a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 11-1.414-1.414L16.586 10l-2.293-2.293a1 1 0 010-1.414z"
                  clipRule="evenodd"
                />
              </svg>
              Advanced RAG Techniques
            </h3>
            <div className="border border-gray-200 rounded-lg p-4 bg-gradient-to-r from-orange-50 to-red-50">
              <h4 className="font-medium text-gray-900 mb-2">
                🚀 Upcoming: GraphRAG
              </h4>
              <p className="text-sm text-gray-600 mb-2">
                We&apos;re excited to bring{" "}
                <a
                  href="https://neo4j.com/use-cases/knowledge-graph/"
                  className="text-blue-600 hover:text-blue-800"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  GraphRAG with Neo4j
                </a>{" "}
                to the platform! GraphRAG combines the power of knowledge graphs
                with RAG to provide even more contextual and accurate responses.
              </p>
              <p className="text-sm text-gray-600">
                This will enable advanced relationship mapping, semantic search
                through connected data, and more sophisticated reasoning
                capabilities.
              </p>
            </div>
          </div>
        </div>

        {/* Community & Learning */}
        <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg p-8">
          <h2 className="text-2xl font-semibold text-gray-900 mb-4">
            Join the Learning Journey
          </h2>
          <p className="text-gray-700 leading-relaxed mb-4">
            RAG Studio is more than just a platform - it&apos;s a community of
            learners, builders, and innovators. Whether you&apos;re a beginner
            curious about RAG or an expert looking to explore new techniques,
            there&apos;s something here for you.
          </p>
          <div className="flex flex-wrap gap-4 mt-6">
            <span className="bg-white bg-opacity-70 px-4 py-2 rounded-full text-sm font-medium text-gray-700 border border-gray-200">
              🎯 Learn by Doing
            </span>
            <span className="bg-white bg-opacity-70 px-4 py-2 rounded-full text-sm font-medium text-gray-700 border border-gray-200">
              🔧 Experiment Safely
            </span>
            <span className="bg-white bg-opacity-70 px-4 py-2 rounded-full text-sm font-medium text-gray-700 border border-gray-200">
              🤝 Share & Collaborate
            </span>
            <span className="bg-white bg-opacity-70 px-4 py-2 rounded-full text-sm font-medium text-gray-700 border border-gray-200">
              🚀 Build Better RAG
            </span>
          </div>
        </div>

        {/* Call to Action */}
        <div className="bg-gray-900 text-white rounded-lg p-8 text-center">
          <h2 className="text-2xl font-semibold mb-4">Ready to Explore RAG?</h2>
          <p className="text-gray-300 text-lg mb-6">
            Dive into the fascinating world of Retrieval-Augmented Generation.
            <br />
            <strong>
              Remember: Have fun, learn, and enjoy this growing space!
            </strong>
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <button className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-6 rounded-lg transition-colors">
              Start Learning
            </button>
            <button className="border border-gray-600 hover:border-gray-500 text-white font-medium py-3 px-6 rounded-lg transition-colors">
              Explore Techniques
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
