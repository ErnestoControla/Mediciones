import React, { useState, useEffect } from 'react';
import { analisisAPI } from '../api/analisis';

const DirectImageTest: React.FC = () => {
  const [imageData, setImageData] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadImage = async () => {
      try {
        setLoading(true);
        const response = await analisisAPI.getMiniaturaAnalisis(26);
        const data = response.thumbnail_data;
        const fullDataUrl = data.startsWith('data:') ? data : `data:image/png;base64,${data}`;
        setImageData(fullDataUrl);
        console.log('🔍 Direct test - Image data loaded:', fullDataUrl.length, 'chars');
      } catch (error) {
        console.error('❌ Direct test - Error loading image:', error);
      } finally {
        setLoading(false);
      }
    };

    loadImage();
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!imageData) {
    return <div>No image data</div>;
  }

  return (
    <div style={{ 
      border: '10px solid green', 
      padding: '20px', 
      backgroundColor: 'white',
      margin: '20px'
    }}>
      <h3>Direct Image Test - Analysis 26</h3>
      <p>Data length: {imageData.length}</p>
      <p>First 100 chars: {imageData.substring(0, 100)}...</p>
      
      <div style={{ 
        border: '5px solid purple', 
        padding: '10px',
        backgroundColor: 'lightblue'
      }}>
        <h4>Image Element:</h4>
        <img
          src={imageData}
          alt="Direct test"
          style={{
            width: '300px',
            height: '300px',
            border: '5px solid orange',
            backgroundColor: 'pink',
            display: 'block',
          }}
          onLoad={() => console.log('✅ Direct test - Image loaded successfully')}
          onError={(e) => console.error('❌ Direct test - Image load error:', e)}
        />
      </div>
    </div>
  );
};

export default DirectImageTest;