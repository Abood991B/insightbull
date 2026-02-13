import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/components/ui/card';
import { Button } from '@/shared/components/ui/button';
import { Input } from '@/shared/components/ui/input';
import { Label } from '@/shared/components/ui/label';
import { Alert, AlertDescription } from '@/shared/components/ui/alert';
import { Loader2, Shield, Copy, CheckCircle, AlertCircle, QrCode } from 'lucide-react';
import { authService } from '../services/auth.service';
import QRCodeDisplay from './QRCodeDisplay';

interface TOTPVerificationProps {
  email: string;
  isNewSetup: boolean;
  onSuccess: () => void;
  onCancel: () => void;
}

const TOTPVerification = ({ email, isNewSetup, onSuccess, onCancel }: TOTPVerificationProps) => {
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [setupData, setSetupData] = useState<{ secret: string; qrCode: string } | null>(null);
  const [secretCopied, setSecretCopied] = useState(false);
  const [step, setStep] = useState<'setup' | 'verify'>(isNewSetup ? 'setup' : 'verify');

  useEffect(() => {
    if (isNewSetup) {
      // Generate new TOTP secret for first-time setup
      const data = authService.generateTotpSecret(email);
      setSetupData(data);
    }
  }, [email, isNewSetup]);

  const handleVerify = async () => {
    if (code.length !== 6) {
      setError('Please enter a 6-digit code');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const isValid = await authService.verifyTotp(email, code);
      
      if (isValid) {
        onSuccess();
      } else {
        setError('Invalid code. Please try again.');
        setCode('');
      }
    } catch (err) {
      if (import.meta.env.DEV) {
        console.error('TOTP verification error:', err);
      }
      setError('Verification failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const copySecret = () => {
    if (setupData?.secret) {
      navigator.clipboard.writeText(setupData.secret);
      setSecretCopied(true);
      setTimeout(() => setSecretCopied(false), 2000);
    }
  };

  const handleCodeChange = (value: string) => {
    // Only allow digits and limit to 6 characters
    const cleaned = value.replace(/\D/g, '').slice(0, 6);
    setCode(cleaned);
    setError(null);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && code.length === 6) {
      handleVerify();
    }
  };

  if (step === 'setup' && setupData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 flex items-center justify-center p-4">
        <Card className="w-full max-w-lg">
          <CardHeader className="space-y-1">
            <div className="flex items-center justify-center mb-4">
              <QrCode className="h-8 w-8 text-blue-600" />
            </div>
            <CardTitle className="text-2xl text-center">Setup Two-Factor Authentication</CardTitle>
            <CardDescription className="text-center">
              Scan the QR code with your authenticator app
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium text-sm mb-2">Step 1: Install an Authenticator App</h4>
                <p className="text-xs text-gray-600">
                  Download one of these apps on your phone:
                </p>
                <ul className="text-xs text-gray-600 mt-2 space-y-1">
                  <li>• Google Authenticator</li>
                  <li>• Microsoft Authenticator</li>
                  <li>• Authy</li>
                </ul>
              </div>

              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium text-sm mb-3">Step 2: Scan QR Code</h4>
                <div className="bg-white p-4 rounded border-2 border-gray-200">
                  <div className="w-48 h-48 mx-auto bg-gray-100 flex items-center justify-center rounded">
                    <QRCodeDisplay qrCodeUrl={setupData.qrCode} />
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium text-sm mb-2">Manual Entry (Alternative)</h4>
                <p className="text-xs text-gray-600 mb-2">
                  Can't scan? Enter this code manually:
                </p>
                <div className="flex items-center space-x-2">
                  <Input
                    value={setupData.secret}
                    readOnly
                    className="font-mono text-xs"
                  />
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={copySecret}
                  >
                    {secretCopied ? (
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    ) : (
                      <Copy className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>

              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription className="text-xs">
                  <strong>Important:</strong> Save this secret key in a secure location. You'll need it to recover access if you lose your authenticator device.
                </AlertDescription>
              </Alert>
            </div>

            <div className="flex space-x-3">
              <Button
                variant="outline"
                onClick={onCancel}
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                onClick={() => setStep('verify')}
                className="flex-1"
              >
                Continue to Verify
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <div className="flex items-center justify-center mb-4">
            <Shield className="h-8 w-8 text-blue-600" />
          </div>
          <CardTitle className="text-2xl text-center">Two-Factor Authentication</CardTitle>
          <CardDescription className="text-center">
            Enter the 6-digit code from your authenticator app
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="space-y-2">
            <Label htmlFor="totp-code">Verification Code</Label>
            <Input
              id="totp-code"
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              maxLength={6}
              value={code}
              onChange={(e) => handleCodeChange(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="000000"
              className="text-center text-2xl font-mono tracking-widest"
              autoComplete="off"
              autoFocus
            />
            <p className="text-xs text-gray-500">
              Enter the code displayed in your authenticator app
            </p>
          </div>

          <div className="flex space-x-3">
            <Button
              variant="outline"
              onClick={onCancel}
              disabled={loading}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              onClick={handleVerify}
              disabled={loading || code.length !== 6}
              className="flex-1"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Verifying...
                </>
              ) : (
                'Verify'
              )}
            </Button>
          </div>

          {isNewSetup && step === 'verify' && (
            <Button
              variant="link"
              onClick={() => setStep('setup')}
              className="w-full text-xs"
            >
              Back to setup instructions
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default TOTPVerification;
