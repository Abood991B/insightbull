import { useEffect, useRef } from 'react';
import { QrCode } from 'lucide-react';

interface QRCodeDisplayProps {
  qrCodeUrl: string;
}

const QRCodeDisplay = ({ qrCodeUrl }: QRCodeDisplayProps) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (canvasRef.current && qrCodeUrl) {
      generateQRCode(qrCodeUrl, canvasRef.current);
    }
  }, [qrCodeUrl]);

  const generateQRCode = (text: string, canvas: HTMLCanvasElement) => {
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const size = 200;
    canvas.width = size;
    canvas.height = size;

    // Use QR Server API as fallback (works without CORS)
    const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(text)}`;
    
    const img = new Image();
    img.crossOrigin = 'anonymous';
    
    img.onload = () => {
      ctx.drawImage(img, 0, 0, size, size);
    };
    
    img.onerror = () => {
      // If external service fails, show instructions
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, size, size);
      ctx.strokeStyle = '#000000';
      ctx.lineWidth = 2;
      ctx.strokeRect(10, 10, size - 20, size - 20);
      
      ctx.fillStyle = '#000000';
      ctx.font = '14px Arial';
      ctx.textAlign = 'center';
      ctx.fillText('QR Code Service', size / 2, size / 2 - 20);
      ctx.fillText('Unavailable', size / 2, size / 2);
      ctx.font = '12px Arial';
      ctx.fillText('Use manual entry below', size / 2, size / 2 + 20);
    };
    
    img.src = qrUrl;
  };

  const generateQRMatrix = (text: string): boolean[][] => {
    // Simplified QR code generation for TOTP URLs
    const size = 25; // QR code version 1 (21x21) + padding
    const matrix: boolean[][] = Array(size).fill(null).map(() => Array(size).fill(false));
    
    // Add finder patterns (position detection patterns)
    addFinderPattern(matrix, 0, 0);
    addFinderPattern(matrix, size - 7, 0);
    addFinderPattern(matrix, 0, size - 7);
    
    // Add timing patterns
    for (let i = 8; i < size - 8; i++) {
      matrix[6][i] = i % 2 === 0;
      matrix[i][6] = i % 2 === 0;
    }
    
    // Add data based on text hash (simplified)
    const hash = simpleHash(text);
    for (let i = 9; i < size - 9; i++) {
      for (let j = 9; j < size - 9; j++) {
        if (!isReservedArea(i, j, size)) {
          matrix[i][j] = ((hash + i * j + i + j) % 3) === 0;
        }
      }
    }
    
    return matrix;
  };

  const addFinderPattern = (matrix: boolean[][], startX: number, startY: number) => {
    // 7x7 finder pattern
    for (let i = 0; i < 7; i++) {
      for (let j = 0; j < 7; j++) {
        const x = startX + i;
        const y = startY + j;
        if (x < matrix.length && y < matrix[0].length) {
          // Outer border and center
          if (i === 0 || i === 6 || j === 0 || j === 6 || (i >= 2 && i <= 4 && j >= 2 && j <= 4)) {
            matrix[x][y] = true;
          }
        }
      }
    }
  };

  const isReservedArea = (x: number, y: number, size: number): boolean => {
    // Check if position is in finder pattern areas or timing patterns
    return (
      (x < 9 && y < 9) || // Top-left finder
      (x >= size - 8 && y < 9) || // Top-right finder
      (x < 9 && y >= size - 8) || // Bottom-left finder
      x === 6 || y === 6 // Timing patterns
    );
  };

  const drawQRCode = (ctx: CanvasRenderingContext2D, matrix: boolean[][], canvasSize: number) => {
    const moduleSize = canvasSize / matrix.length;
    
    // Clear canvas
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvasSize, canvasSize);
    
    // Draw QR modules
    ctx.fillStyle = '#000000';
    for (let i = 0; i < matrix.length; i++) {
      for (let j = 0; j < matrix[i].length; j++) {
        if (matrix[i][j]) {
          ctx.fillRect(i * moduleSize, j * moduleSize, moduleSize, moduleSize);
        }
      }
    }
  };

  const simpleHash = (str: string): number => {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash);
  };

  const drawFinderPattern = (ctx: CanvasRenderingContext2D, x: number, y: number, moduleSize: number) => {
    // Draw 7x7 finder pattern
    ctx.fillStyle = '#000000';
    ctx.fillRect(x, y, 7 * moduleSize, 7 * moduleSize);
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(x + moduleSize, y + moduleSize, 5 * moduleSize, 5 * moduleSize);
    ctx.fillStyle = '#000000';
    ctx.fillRect(x + 2 * moduleSize, y + 2 * moduleSize, 3 * moduleSize, 3 * moduleSize);
  };

  return (
    <div className="text-center">
      <canvas 
        ref={canvasRef}
        className="border rounded"
        style={{ maxWidth: '200px', maxHeight: '200px' }}
      />
      <p className="text-xs text-gray-500 mt-2">
        Scan with your authenticator app
      </p>
      <p className="text-xs text-gray-400">
        Or use manual entry below
      </p>
    </div>
  );
};

export default QRCodeDisplay;
