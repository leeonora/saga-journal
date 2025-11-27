"use client";

import Image from 'next/image';

export function LoadingScreen() {
  return (
    <div className="fixed inset-0 bg-[#fcfcff] z-50 flex items-center justify-center">
      <div className="flex flex-col items-center">
        {/* 
          TODO: Replace this with the actual path to your loading GIF.
          You can download a suitable GIF from sites like GIPHY or Tenor.
          Make sure to place the GIF in the `public` directory of your `saga-frontend` project.
        */}
        <Image 
          src="/loading.gif" // Replace with your GIF file name
          alt="Loading..." 
          width={400} 
          height={400} 
          unoptimized // Required for animated GIFs
        />
        <p className="mt-4 text-lg text-muted-foreground">Loading your saga...</p>
      </div>
    </div>
  );
}
