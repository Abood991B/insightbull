import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/components/ui/card';
import { Button } from '@/shared/components/ui/button';
import { Alert, AlertDescription } from '@/shared/components/ui/alert';
import { Loader2, Shield, AlertCircle } from 'lucide-react';
import { authService } from '../services/auth.service';
import { securityConfig } from '../config/security.config';
import TOTPVerification from './TOTPVerification';

const OAuth2AdminAuth = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [step, setStep] = useState<'oauth' | 'totp' | 'complete'>('oauth');
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    // Check if already authenticated
    if (authService.isFullyAuthenticated()) {
      navigate('/admin/dashboard');
      return;
    }

    // Handle OAuth callback
    const code = searchParams.get('code');
    const error = searchParams.get('error');

    if (error) {
      setError('Authentication failed: ' + error);
      return;
    }

    if (code) {
      handleOAuthCallback(code);
    }
  }, [searchParams, navigate]);

  const handleOAuthCallback = async (code: string) => {
    setLoading(true);
    setError(null);

    try {
      const result = await authService.authenticateWithGoogle(code);
      
      if (!result.success) {
        setError(result.error || 'Authentication failed');
        setLoading(false);
        return;
      }

      if (result.user) {
        setUser(result.user);
        
        // Check if TOTP is required
        if (result.user.totpEnabled) {
          setStep('totp');
        } else {
          // First-time setup - show TOTP setup
          setStep('totp');
        }
      }
    } catch (err) {
      console.error('OAuth callback error:', err);
      setError('An unexpected error occurred during authentication');
    } finally {
      setLoading(false);
    }
  };

  const initiateOAuth = () => {
    const params = new URLSearchParams({
      client_id: securityConfig.oauth2.clientId,
      redirect_uri: securityConfig.oauth2.redirectUri,
      response_type: 'code',
      scope: securityConfig.oauth2.scope,
      access_type: 'offline',
      prompt: 'select_account',
    });

    window.location.href = `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`;
  };

  const handleTOTPSuccess = () => {
    setStep('complete');
    setTimeout(() => {
      navigate('/admin/dashboard');
    }, 1500);
  };

  const handleTOTPCancel = () => {
    authService.logout();
    setStep('oauth');
    setUser(null);
    setError('Authentication cancelled. Please try again.');
  };

  if (step === 'totp' && user) {
    return (
      <TOTPVerification
        email={user.email}
        isNewSetup={!user.totpEnabled}
        onSuccess={handleTOTPSuccess}
        onCancel={handleTOTPCancel}
      />
    );
  }

  if (step === 'complete') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6">
            <div className="text-center">
              <div className="mx-auto w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mb-4">
                <Shield className="h-6 w-6 text-green-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900">Authentication Successful</h3>
              <p className="text-sm text-gray-600 mt-2">Redirecting to admin dashboard...</p>
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
          <CardTitle className="text-2xl text-center">Admin Authentication</CardTitle>
          <CardDescription className="text-center">
            Secure access to the admin panel
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="space-y-4">
            <div className="text-sm text-gray-600 space-y-2">
              <p className="font-medium">Security Requirements:</p>
              <ul className="list-disc list-inside space-y-1 text-xs">
                <li>Google account authentication required</li>
                <li>Email must be on the authorized admin list</li>
                <li>Two-factor authentication (TOTP) verification</li>
                <li>Session expires after 30 minutes of inactivity</li>
              </ul>
            </div>

            <Button
              onClick={initiateOAuth}
              disabled={loading}
              className="w-full"
              size="lg"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Authenticating...
                </>
              ) : (
                <>
                  <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24">
                    <path
                      fill="currentColor"
                      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                    />
                    <path
                      fill="currentColor"
                      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    />
                    <path
                      fill="currentColor"
                      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                    />
                    <path
                      fill="currentColor"
                      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                    />
                  </svg>
                  Sign in with Google
                </>
              )}
            </Button>
          </div>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-white px-2 text-gray-500">Security Notice</span>
            </div>
          </div>

          <div className="text-xs text-gray-500 text-center space-y-1">
            <p>This is a restricted area. Unauthorized access is prohibited.</p>
            <p>All authentication attempts are logged and monitored.</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default OAuth2AdminAuth;
