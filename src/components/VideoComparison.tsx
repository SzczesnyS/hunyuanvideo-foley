import React from 'react';

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

interface VideoComparisonProps {
  data: VideoData;
}

const methodNames = {
  'hifi-foley': 'HunyuanVideo-Foley (Ours)',
  mmaudio: 'MMAudio',
  foleycrafer: 'FoleyCrafter',
  thinksound: 'ThinkSound'
};

export const VideoComparison: React.FC<VideoComparisonProps> = ({ data }) => {
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

interface VideoComparisonGridProps {
  dataList: VideoData[];
}

export const VideoComparisonGrid: React.FC<VideoComparisonGridProps> = ({ dataList }) => {
  return (
    <div className="w-full -mx-6 px-6 space-y-8">
      {dataList.map((data) => (
        <VideoComparison key={data.sequence_id} data={data} />
      ))}
    </div>
  );
};