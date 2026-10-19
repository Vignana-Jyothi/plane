import React from "react";

export default function PublicMemberProfile({ params }: { params: { slug: string } }) {
  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col gap-8 p-8">
      <div className="border-custom-border-200 flex items-center gap-6 border-b pb-6">
        <div className="bg-custom-background-200 h-24 w-24 rounded-full" />
        <div>
          <h1 className="text-3xl text-custom-text-100 font-bold">{params.slug}'s Portfolio</h1>
          <p className="text-lg text-custom-text-200 mt-1">VJ Startups OS Contributor</p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <div className="border-custom-border-200 bg-custom-background-100 rounded-lg border p-6 md:col-span-1">
          <h2 className="text-xl mb-4 font-semibold">Reputation</h2>
          <div className="text-4xl text-primary-100 font-bold">--</div>
          <div className="text-sm text-custom-text-200 mt-1">Global Rank: #--</div>
        </div>

        <div className="border-custom-border-200 bg-custom-background-100 rounded-lg border p-6 md:col-span-2">
          <h2 className="text-xl mb-4 font-semibold">Recent Contributions</h2>
          <ul className="space-y-4">
            <li className="text-custom-text-200">No recent contributions found.</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
