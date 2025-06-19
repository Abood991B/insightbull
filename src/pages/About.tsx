
import UserLayout from "@/components/UserLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const About = () => {
  return (
    <UserLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">About This Dashboard</h1>
          <p className="text-gray-600 mt-2">Learn about our sentiment analysis system and methodology</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>What We Do</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p>
                Our platform analyzes real-time sentiment data from multiple sources including Reddit, 
                news articles, and social media to provide insights into stock market sentiment.
              </p>
              <p>
                We track the top technology stocks including the Magnificent Seven (AAPL, GOOGL, MSFT, 
                TSLA, NVDA, META, AMZN) and the top 20 IXT stocks.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Our Technology</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p>
                We use advanced NLP models including VADER for social media sentiment and FinBERT 
                for financial news analysis to provide accurate sentiment scoring.
              </p>
              <p>
                Our system processes thousands of data points daily, providing real-time correlation 
                analysis between sentiment and stock price movements.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Data Sources</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <ul className="list-disc list-inside space-y-2">
                <li>Reddit - Social media sentiment analysis</li>
                <li>FinHub - Financial news and data</li>
                <li>NewsAPI - Global news sentiment</li>
                <li>Marketaux - Market news and analysis</li>
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>How to Use</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <ol className="list-decimal list-inside space-y-2">
                <li>Select your preferred stock from the dropdown menu</li>
                <li>Choose your time range (1 day to 30 days)</li>
                <li>Explore different analysis views: sentiment vs price, correlations, and trends</li>
                <li>Use the dashboard to identify patterns and make informed decisions</li>
              </ol>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Methodology</CardTitle>
            <CardDescription>How we calculate sentiment scores and correlations</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-semibold mb-2">Sentiment Analysis</h3>
                <p className="text-sm text-gray-600">
                  Sentiment scores range from -1 (most negative) to +1 (most positive). 
                  We aggregate individual post/article sentiments by stock and time period.
                </p>
              </div>
              <div>
                <h3 className="font-semibold mb-2">Correlation Analysis</h3>
                <p className="text-sm text-gray-600">
                  We use Pearson correlation coefficients to measure the relationship 
                  between sentiment scores and stock price movements over selected time periods.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </UserLayout>
  );
};

export default About;
