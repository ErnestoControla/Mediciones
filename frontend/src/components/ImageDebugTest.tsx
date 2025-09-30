import React, { useState, useEffect } from 'react';
import { analisisAPI } from '../api/analisis';

const ImageDebugTest: React.FC = () => {
  const [imageData, setImageData] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadImage = async () => {
      try {
        setLoading(true);
        setError(null);
        
        console.log('🔍 Loading image for analysis 26...');
        const response = await analisisAPI.getMiniaturaAnalisis(26);
        const data = response.thumbnail_data;
        const fullDataUrl = data.startsWith('data:') ? data : `data:image/png;base64,${data}`;
        
        console.log('📦 Image data received:', {
          length: fullDataUrl.length,
          startsWithData: fullDataUrl.startsWith('data:'),
          first100: fullDataUrl.substring(0, 100)
        });
        
        setImageData(fullDataUrl);
      } catch (err) {
        console.error('❌ Error loading image:', err);
        setError('Error loading image');
      } finally {
        setLoading(false);
      }
    };

    loadImage();
  }, []);

  if (loading) {
    return <div style={{ padding: '20px', border: '2px solid blue' }}>Loading...</div>;
  }

  if (error) {
    return <div style={{ padding: '20px', border: '2px solid red' }}>Error: {error}</div>;
  }

  if (!imageData) {
    return <div style={{ padding: '20px', border: '2px solid orange' }}>No image data</div>;
  }

  return (
    <div style={{ 
      border: '10px solid green', 
      padding: '30px', 
      backgroundColor: 'white',
      margin: '20px'
    }}>
      <h2 style={{ color: 'black', margin: '0 0 20px 0' }}>
        Image Debug Test - Analysis 26
      </h2>
      
      <div style={{ marginBottom: '20px' }}>
        <h3 style={{ color: 'black' }}>Image Data Info:</h3>
        <p style={{ color: 'black' }}>Length: {imageData.length} characters</p>
        <p style={{ color: 'black' }}>Format: {imageData.startsWith('data:') ? 'Data URL' : 'Raw Base64'}</p>
        <p style={{ color: 'black' }}>First 100 chars: {imageData.substring(0, 100)}...</p>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h3 style={{ color: 'black' }}>Image Display Test:</h3>
        <div style={{
          border: '5px solid purple',
          padding: '20px',
          backgroundColor: 'lightgray',
          display: 'inline-block'
        }}>
          <img
            src={imageData}
            alt="Debug test image"
            style={{
              width: '400px',
              height: '400px',
              border: '5px solid red',
              backgroundColor: 'yellow',
              display: 'block',
              objectFit: 'contain'
            }}
            onLoad={(e) => {
              const img = e.target as HTMLImageElement;
              console.log('✅ Image loaded successfully');
              console.log('Natural dimensions:', img.naturalWidth, 'x', img.naturalHeight);
              console.log('Display dimensions:', img.width, 'x', img.height);
              console.log('Image visible:', img.offsetWidth > 0 && img.offsetHeight > 0);
              console.log('Image complete:', img.complete);
            }}
            onError={(e) => {
              console.error('❌ Image load error:', e);
            }}
          />
        </div>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h3 style={{ color: 'black' }}>Raw Data URL (first 200 chars):</h3>
        <textarea
          value={imageData.substring(0, 200)}
          readOnly
          style={{
            width: '100%',
            height: '100px',
            border: '2px solid black',
            padding: '10px',
            fontFamily: 'monospace',
            fontSize: '12px'
          }}
        />
      </div>
    </div>
  );
};

export default ImageDebugTest;
