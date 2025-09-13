
import AdminLayout from "@/shared/components/layouts/AdminLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import { Badge } from "@/shared/components/ui/badge";
import { useState } from "react";
import { useToast } from "@/shared/hooks/use-toast";

const ApiConfig = () => {
  const [redditKey, setRedditKey] = useState("");
  const [finHubKey, setFinHubKey] = useState("");
  const [newsApiKey, setNewsApiKey] = useState("");
  const [marketauxKey, setMarketauxKey] = useState("");
  const { toast } = useToast();

  const handleSave = () => {
    toast({
      title: "API Keys Updated",
      description: "All API configurations have been saved successfully.",
    });
  };

  const apiStatuses = [
    { name: "Reddit API", status: "Connected", color: "green" },
    { name: "FinHub API", status: "Connected", color: "green" },
    { name: "NewsAPI", status: "Rate Limited", color: "yellow" },
    { name: "Marketaux API", status: "Connected", color: "green" },
  ];

  return (
    <AdminLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">API Configuration</h1>
          <p className="text-gray-600 mt-2">Manage external API keys and connections</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>API Status Overview</CardTitle>
            <CardDescription>Current status of all external API connections</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {apiStatuses.map((api) => (
                <div key={api.name} className="text-center">
                  <h3 className="font-medium mb-2">{api.name}</h3>
                  <Badge 
                    className={`${
                      api.color === 'green' ? 'bg-green-100 text-green-800' :
                      api.color === 'yellow' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}
                  >
                    {api.status}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Reddit API</CardTitle>
              <CardDescription>Configuration for Reddit data collection</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="reddit-key">API Key</Label>
                <Input
                  id="reddit-key"
                  type="password"
                  value={redditKey}
                  onChange={(e) => setRedditKey(e.target.value)}
                  placeholder="Enter Reddit API key"
                />
              </div>
              <Button onClick={handleSave} className="w-full">
                Update Reddit API
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>FinHub API</CardTitle>
              <CardDescription>Configuration for financial data</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="finhub-key">API Key</Label>
                <Input
                  id="finhub-key"
                  type="password"
                  value={finHubKey}
                  onChange={(e) => setFinHubKey(e.target.value)}
                  placeholder="Enter FinHub API key"
                />
              </div>
              <Button onClick={handleSave} className="w-full">
                Update FinHub API
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>NewsAPI</CardTitle>
              <CardDescription>Configuration for news data collection</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="news-key">API Key</Label>
                <Input
                  id="news-key"
                  type="password"
                  value={newsApiKey}
                  onChange={(e) => setNewsApiKey(e.target.value)}
                  placeholder="Enter NewsAPI key"
                />
              </div>
              <Button onClick={handleSave} className="w-full">
                Update NewsAPI
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Marketaux API</CardTitle>
              <CardDescription>Configuration for market news</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="marketaux-key">API Key</Label>
                <Input
                  id="marketaux-key"
                  type="password"
                  value={marketauxKey}
                  onChange={(e) => setMarketauxKey(e.target.value)}
                  placeholder="Enter Marketaux API key"
                />
              </div>
              <Button onClick={handleSave} className="w-full">
                Update Marketaux API
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </AdminLayout>
  );
};

export default ApiConfig;
