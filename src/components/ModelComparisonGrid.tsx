import React, { useState, useMemo } from 'react';

interface ModelComparisonVideoData {
  sequence_id: number;
  video_id: string;
  prompt: string;
  videos: {
    [key: string]: string;
  };
}

interface ModelComparisonGridProps {
  dataList: ModelComparisonVideoData[];
  itemsPerPage?: number;
}

const methodNames = {
  'hifi-foley': 'HIFI-Foley (Ours)',
  'foleycrafter': 'FoleyCrafter',
  'mmaudio': 'MMAudio',
  'thinksound': 'ThinkSound',
  'v-aura': 'V-AURA',
  'frieren': 'Frieren'
};

const methodOrder = ['hifi-foley', 'foleycrafter', 'mmaudio', 'thinksound', 'v-aura', 'frieren'];

const VideoCard: React.FC<{ method: string; videoPath: string; videoId: string }> = ({ 
  method, 
  videoPath, 
  videoId 
}) => {
  return (
    <div className="bg-white dark:bg-gray-700 rounded-xl p-4 shadow-lg border border-gray-200 dark:border-gray-600 hover:shadow-xl transition-shadow duration-300">
      <h5 className="text-sm font-semibold mb-3 text-center border-b border-gray-200 dark:border-gray-600 pb-2">
        {methodNames[method as keyof typeof methodNames] || method}
      </h5>
      <video
        controls
        className="w-full h-auto rounded-lg shadow-md hover:shadow-lg transition-shadow duration-300"
        preload="metadata"
        style={{ minHeight: '150px', aspectRatio: '16/9' }}
      >
        <source src={videoPath} type="video/mp4" />
        Your browser does not support the video tag.
      </video>
    </div>
  );
};

const VideoComparison: React.FC<{ data: ModelComparisonVideoData }> = ({ data }) => {
  // Sort videos according to methodOrder
  const sortedVideos = useMemo(() => {
    return methodOrder
      .filter(method => data.videos[method])
      .map(method => [method, data.videos[method]] as [string, string]);
  }, [data.videos]);

  return (
    <div className="mb-12 p-8 bg-gray-50 dark:bg-gray-800 rounded-xl shadow-lg">
      <div className="mb-6">
        <h4 className="text-xl font-semibold mb-2">Video ID: {data.video_id}</h4>
        <p className="text-gray-600 dark:text-gray-300 text-sm bg-white dark:bg-gray-700 p-3 rounded-lg border-l-4 border-blue-500">
          <strong>Prompt:</strong> {data.prompt}
        </p>
      </div>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-6">
        {sortedVideos.map(([method, videoPath]) => (
          <VideoCard
            key={method}
            method={method}
            videoPath={videoPath}
            videoId={data.video_id}
          />
        ))}
      </div>
    </div>
  );
};

const PaginationControls: React.FC<{
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}> = ({ currentPage, totalPages, onPageChange }) => {
  const getPageNumbers = () => {
    const pages = [];
    const maxPagesToShow = 7;
    
    if (totalPages <= maxPagesToShow) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      if (currentPage <= 4) {
        for (let i = 1; i <= 5; i++) pages.push(i);
        pages.push('...');
        pages.push(totalPages);
      } else if (currentPage >= totalPages - 3) {
        pages.push(1);
        pages.push('...');
        for (let i = totalPages - 4; i <= totalPages; i++) pages.push(i);
      } else {
        pages.push(1);
        pages.push('...');
        for (let i = currentPage - 1; i <= currentPage + 1; i++) pages.push(i);
        pages.push('...');
        pages.push(totalPages);
      }
    }
    
    return pages;
  };

  return (
    <div className="flex items-center justify-center space-x-2 py-8">
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="px-4 py-2 text-sm font-medium text-gray-500 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
      >
        Previous
      </button>
      
      {getPageNumbers().map((page, index) => (
        <React.Fragment key={index}>
          {page === '...' ? (
            <span className="px-4 py-2 text-sm text-gray-500">...</span>
          ) : (
            <button
              onClick={() => onPageChange(page as number)}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors duration-200 ${
                currentPage === page
                  ? 'bg-blue-600 text-white border border-blue-600'
                  : 'text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600'
              }`}
            >
              {page}
            </button>
          )}
        </React.Fragment>
      ))}
      
      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="px-4 py-2 text-sm font-medium text-gray-500 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
      >
        Next
      </button>
    </div>
  );
};

export const ModelComparisonGrid: React.FC<ModelComparisonGridProps> = ({ 
  dataList, 
  itemsPerPage = 4 
}) => {
  const [currentPage, setCurrentPage] = useState(1);
  const containerRef = React.useRef<HTMLDivElement>(null);
  
  const totalPages = Math.ceil(dataList.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentData = dataList.slice(startIndex, endIndex);
  
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    // Scroll to top of the comparison grid component instead of entire page
    if (containerRef.current) {
      containerRef.current.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'start' 
      });
    }
  };

  return (
    <div ref={containerRef} className="w-full -mx-6 px-6">
      {/* Video comparisons */}
      <div className="space-y-8">
        {currentData.map((data) => (
          <VideoComparison key={data.sequence_id} data={data} />
        ))}
      </div>
      
      {/* Pagination */}
      {totalPages > 1 && (
        <PaginationControls
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={handlePageChange}
        />
      )}
    </div>
  );
};