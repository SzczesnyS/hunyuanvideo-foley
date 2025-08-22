import React, { useState } from 'react';

interface VideoData {
  sequence_id: number;
  chinese_prompt: string;
  english_prompt: string;
  videos: {
    'hifi-foley': string;
    mmaudio: string;
    foleycrafer: string;
    thinksound: string;
  };
}

interface LazyVideoComparisonGridProps {
  dataList: VideoData[];
  initialCount?: number;
}

const methodNames = {
  'hifi-foley': 'HunyuanVideo-Foley (Ours)',
  mmaudio: 'MMAudio',
  foleycrafer: 'FoleyCrafter',
  thinksound: 'ThinkSound'
};

const VideoComparison: React.FC<{ data: VideoData }> = ({ data }) => {
  return (
    <div className="mb-12 p-8 bg-gray-50 dark:bg-gray-800 rounded-xl shadow-lg">
      <div className="mb-6">
        <h4 className="text-xl font-semibold mb-3">Sample {data.sequence_id}</h4>
        <div className="text-base text-gray-700 dark:text-gray-300 mb-4 leading-relaxed">
          <strong>Prompt:</strong> {data.english_prompt}
        </div>
      </div>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8 2xl:gap-10">
        {Object.entries(data.videos).map(([method, videoPath]) => (
          <div key={method} className="bg-white dark:bg-gray-700 rounded-xl p-6 shadow-lg border border-gray-200 dark:border-gray-600">
            <h5 className="text-lg font-semibold mb-4 text-center border-b border-gray-200 dark:border-gray-600 pb-3">
              {methodNames[method as keyof typeof methodNames]}
            </h5>
            <video
              controls
              className="w-full h-auto rounded-lg shadow-md hover:shadow-lg transition-shadow duration-300"
              preload="metadata"
              style={{ minHeight: '250px', aspectRatio: '16/9' }}
            >
              <source src={`/${videoPath}`} type="video/mp4" />
              Your browser does not support the video tag.
            </video>
          </div>
        ))}
      </div>
    </div>
  );
};

export const LazyVideoComparisonGrid: React.FC<LazyVideoComparisonGridProps> = ({ 
  dataList, 
  initialCount = 5 
}) => {
  const [showAll, setShowAll] = useState(false);
  
  const displayedData = showAll ? dataList : dataList.slice(0, initialCount);
  
  return (
    <div className="w-full -mx-6 px-6 space-y-8">
      {displayedData.map((data) => (
        <VideoComparison key={data.sequence_id} data={data} />
      ))}
      
      {!showAll && dataList.length > initialCount && (
        <div className="text-center py-8">
          <button
            onClick={() => setShowAll(true)}
            className="inline-flex items-center px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-300 ease-in-out"
          >
            <svg 
              className="w-5 h-5 mr-3" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth="2" 
                d="M19 9l-7 7-7-7"
              />
            </svg>
            Show All Results ({dataList.length - initialCount} more)
          </button>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-4 max-w-md mx-auto">
            ⚠️ <strong>Performance Notice:</strong> Loading all videos may cause slower page rendering due to the large number of media files.
          </p>
        </div>
      )}
      
      {showAll && (
        <div className="text-center py-4">
          <button
            onClick={() => setShowAll(false)}
            className="inline-flex items-center px-6 py-3 bg-gray-600 hover:bg-gray-700 text-white font-medium rounded-lg shadow hover:shadow-lg transition-all duration-200"
          >
            <svg 
              className="w-4 h-4 mr-2" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth="2" 
                d="M5 15l7-7 7 7"
              />
            </svg>
            Show Less
          </button>
        </div>
      )}
    </div>
  );
};