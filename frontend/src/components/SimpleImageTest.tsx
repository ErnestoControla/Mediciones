import React from 'react';

const SimpleImageTest: React.FC = () => {
  // Test with a simple base64 image
  const testImageData = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==";
  
  return (
    <div style={{ padding: '20px', border: '2px solid red' }}>
      <h3>Test de Imagen Simple</h3>
      <img 
        src={testImageData}
        alt="Test"
        style={{ 
          width: '100px', 
          height: '100px', 
          border: '2px solid blue',
          backgroundColor: 'lightgray'
        }}
        onLoad={() => console.log('✅ Test image loaded')}
        onError={(e) => console.error('❌ Test image error:', e)}
      />
    </div>
  );
};

export default SimpleImageTest;