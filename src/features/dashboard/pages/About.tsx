
import UserLayout from "@/shared/components/layouts/UserLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Badge } from "@/shared/components/ui/badge";
import { TrendingUp, BarChart3, Activity, Database, Zap, Shield } from "lucide-react";

const About = () => {
  const features = [
    {
      icon: TrendingUp,
      title: "Near-Real-Time Analysis",
      description: "Advanced sentiment analysis with minimal latency for timely insights"
    },
    {
      icon: BarChart3,
      title: "Statistical Correlation",
      description: "Pearson correlation analysis and R-squared calculations for statistical validity"
    },
    {
      icon: Activity,
      title: "Multi-Source Data",
      description: "Aggregated data from Reddit, news APIs, and financial sources"
    },
    {
      icon: Database,
      title: "Comprehensive Coverage",
      description: "20 top technology stocks including Microsoft, NVIDIA, Apple, and more"
    },
    {
      icon: Zap,
      title: "Advanced NLP",
      description: "Hybrid VADER and FinBERT models for accurate sentiment classification"
    },
    {
      icon: Shield,
      title: "Data Quality",
      description: "Rigorous data validation and noise filtering for reliable insights"
    }
  ];

  const dataSourceCard = [
    { name: "Reddit", description: "Social media sentiment from financial communities", badge: "Social" },
    { name: "FinHub", description: "Professional financial news and market data", badge: "News" },
    { name: "NewsAPI", description: "Global news sentiment analysis", badge: "News" },
    { name: "Marketaux", description: "Market news and real-time analysis", badge: "Market" }
  ];

  const stocks = [
    "MSFT - Microsoft Corp", "NVDA - NVIDIA Corp", "AAPL - Apple Inc.", "AVGO - Broadcom Inc",
    "ORCL - Oracle Corp.", "PLTR - Palantir Technologies", "IBM - International Business Machines",
    "CSCO - Cisco Systems", "CRM - Salesforce Inc.", "INTU - Intuit Inc."
  ];

  return (
    <UserLayout>
      <div className="space-y-8">
        {/* Hero Section */}
        <div className="text-center py-8 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">About Our Near-Real-Time Dashboard</h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Advanced sentiment analysis platform providing statistical insights into technology stock performance 
            through near-real-time data processing and correlation analysis.
          </p>
        </div>

        {/* Key Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <Card key={index} className="hover:shadow-lg transition-shadow border-l-4 border-l-blue-500">
              <CardHeader className="pb-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <feature.icon className="h-6 w-6 text-blue-600" />
                  </div>
                  <CardTitle className="text-lg">{feature.title}</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">{feature.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* What We Do */}
          <Card className="h-fit">
            <CardHeader>
              <CardTitle className="text-2xl flex items-center gap-3">
                <TrendingUp className="h-7 w-7 text-blue-600" />
                What We Analyze
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-gray-700 leading-relaxed">
                Our platform processes near-real-time sentiment data from multiple sources to provide 
                comprehensive insights into technology stock market sentiment patterns and price correlations.
              </p>
              <p className="text-gray-700 leading-relaxed">
                We focus on the top 20 technology stocks, providing statistical analysis including 
                Pearson correlation coefficients, R-squared values, and significance testing to ensure 
                data-driven insights.
              </p>
              <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                <h4 className="font-semibold text-blue-900 mb-2">Coverage Includes:</h4>
                <div className="grid grid-cols-1 gap-1">
                  {stocks.slice(0, 5).map((stock, index) => (
                    <Badge key={index} variant="outline" className="text-sm justify-start">
                      {stock}
                    </Badge>
                  ))}
                  <Badge variant="secondary" className="text-sm justify-center">
                    +15 more technology leaders
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Technology Stack */}
          <Card className="h-fit">
            <CardHeader>
              <CardTitle className="text-2xl flex items-center gap-3">
                <Zap className="h-7 w-7 text-green-600" />
                Our Technology
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-gray-700 leading-relaxed">
                We employ advanced Natural Language Processing models including Hybrid VADER (Enhanced VADER + ML ensemble) for social media 
                sentiment and FinBERT for financial news analysis, ensuring accurate sentiment classification with 91.67% accuracy.
              </p>
              <p className="text-gray-700 leading-relaxed">
                Our system processes thousands of data points daily, providing statistical correlation 
                analysis between sentiment trends and stock price movements with rigorous significance testing.
              </p>
              <div className="mt-4 space-y-3">
                <div className="p-3 bg-green-50 rounded-lg">
                  <h4 className="font-semibold text-green-900">NLP Models</h4>
                  <p className="text-sm text-green-700">Hybrid VADER, FinBERT, Custom Classification</p>
                </div>
                <div className="p-3 bg-purple-50 rounded-lg">
                  <h4 className="font-semibold text-purple-900">Statistical Methods</h4>
                  <p className="text-sm text-purple-700">Pearson Correlation, R-squared, Significance Testing</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Data Sources */}
        <Card>
          <CardHeader>
            <CardTitle className="text-2xl flex items-center gap-3">
              <Database className="h-7 w-7 text-purple-600" />
              Data Sources & Quality
            </CardTitle>
            <CardDescription>
              Multiple validated data streams ensure comprehensive market sentiment coverage
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {dataSourceCard.map((source, index) => (
                <div key={index} className="p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold text-lg">{source.name}</h3>
                    <Badge variant="outline">{source.badge}</Badge>
                  </div>
                  <p className="text-gray-600 text-sm">{source.description}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Methodology */}
        <Card>
          <CardHeader>
            <CardTitle className="text-2xl flex items-center gap-3">
              <BarChart3 className="h-7 w-7 text-orange-600" />
              Statistical Methodology
            </CardTitle>
            <CardDescription>How we calculate sentiment scores and statistical correlations</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="space-y-4">
                <div className="p-4 bg-orange-50 rounded-lg">
                  <h3 className="font-semibold mb-3 text-orange-900">Sentiment Analysis Process</h3>
                  <ul className="space-y-2 text-sm text-orange-800">
                    <li>Sentiment scores range from -1 (negative) to +1 (positive)</li>
                    <li>Multi-model ensemble for improved accuracy</li>
                    <li>Temporal aggregation by stock and time period</li>
                    <li>Noise filtering and outlier detection</li>
                  </ul>
                </div>
              </div>
              <div className="space-y-4">
                <div className="p-4 bg-blue-50 rounded-lg">
                  <h3 className="font-semibold mb-3 text-blue-900">Correlation Analysis</h3>
                  <ul className="space-y-2 text-sm text-blue-800">
                    <li>Pearson correlation coefficients with confidence intervals</li>
                    <li>R-squared values for variance explanation</li>
                    <li>Statistical significance testing (p-values)</li>
                    <li>Cross-validation for model reliability</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Usage Guide */}
            <div className="mt-8 p-6 bg-gradient-to-r from-gray-50 to-gray-100 rounded-lg">
              <h3 className="font-semibold text-xl mb-4 text-gray-900">How to Use the Dashboard</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <ol className="list-decimal list-inside space-y-2 text-gray-700">
                  <li>Select your preferred stock from our 20-stock technology watchlist</li>
                  <li>Choose your analysis timeframe (1, 7, or 14 days)</li>
                  <li>Explore sentiment vs price correlations and statistical significance</li>
                  <li>Analyze trend patterns and momentum indicators</li>
                </ol>
                <div className="space-y-2">
                  <Badge className="bg-green-100 text-green-800">Near-Real-Time Updates</Badge>
                  <Badge className="bg-blue-100 text-blue-800">Statistical Validation</Badge>
                  <Badge className="bg-purple-100 text-purple-800">Multi-Source Analysis</Badge>
                  <Badge className="bg-orange-100 text-orange-800">Professional Grade</Badge>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </UserLayout>
  );
};

export default About;
