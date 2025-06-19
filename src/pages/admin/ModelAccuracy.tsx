
import AdminLayout from "@/components/AdminLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

const ModelAccuracy = () => {
  return (
    <AdminLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Model Accuracy</h1>
          <p className="text-gray-600 mt-2">Performance metrics for sentiment analysis models</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>VADER Model (Reddit Data)</CardTitle>
              <CardDescription>Social media sentiment analysis performance</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex justify-between items-center">
                <span>Accuracy</span>
                <div className="flex items-center gap-2">
                  <Progress value={85} className="w-20" />
                  <span className="text-sm font-medium">85%</span>
                </div>
              </div>
              <div className="flex justify-between items-center">
                <span>Precision</span>
                <div className="flex items-center gap-2">
                  <Progress value={82} className="w-20" />
                  <span className="text-sm font-medium">82%</span>
                </div>
              </div>
              <div className="flex justify-between items-center">
                <span>Recall</span>
                <div className="flex items-center gap-2">
                  <Progress value={88} className="w-20" />
                  <span className="text-sm font-medium">88%</span>
                </div>
              </div>
              <div className="flex justify-between items-center">
                <span>F1-Score</span>
                <div className="flex items-center gap-2">
                  <Progress value={85} className="w-20" />
                  <span className="text-sm font-medium">85%</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>FinBERT Model (News Data)</CardTitle>
              <CardDescription>Financial news sentiment analysis performance</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex justify-between items-center">
                <span>Accuracy</span>
                <div className="flex items-center gap-2">
                  <Progress value={92} className="w-20" />
                  <span className="text-sm font-medium">92%</span>
                </div>
              </div>
              <div className="flex justify-between items-center">
                <span>Precision</span>
                <div className="flex items-center gap-2">
                  <Progress value={90} className="w-20" />
                  <span className="text-sm font-medium">90%</span>
                </div>
              </div>
              <div className="flex justify-between items-center">
                <span>Recall</span>
                <div className="flex items-center gap-2">
                  <Progress value={94} className="w-20" />
                  <span className="text-sm font-medium">94%</span>
                </div>
              </div>
              <div className="flex justify-between items-center">
                <span>F1-Score</span>
                <div className="flex items-center gap-2">
                  <Progress value={92} className="w-20" />
                  <span className="text-sm font-medium">92%</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Model Evaluation Summary</CardTitle>
            <CardDescription>Overall performance and recommendations</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <Badge className="bg-green-100 text-green-800 mb-2">Excellent</Badge>
                <p className="text-sm text-gray-600">FinBERT performance on financial news</p>
              </div>
              <div className="text-center">
                <Badge className="bg-blue-100 text-blue-800 mb-2">Good</Badge>
                <p className="text-sm text-gray-600">VADER performance on social media</p>
              </div>
              <div className="text-center">
                <Badge className="bg-yellow-100 text-yellow-800 mb-2">Monitor</Badge>
                <p className="text-sm text-gray-600">Continue monitoring for improvements</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </AdminLayout>
  );
};

export default ModelAccuracy;
