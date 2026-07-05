import React from "react";

export default function PublicMemberProfile({ params }: { params: { slug: string } }) {
  return (
    <div className="w-full max-w-4xl mx-auto p-8 flex flex-col gap-8">
      <div className="flex items-center gap-6 pb-6 border-b border-custom-border-200">
        <div className="w-24 h-24 rounded-full bg-custom-background-200" />
        <div>
          <h1 className="text-3xl font-bold text-custom-text-100">
            {params.slug}'s Portfolio
          </h1>
          <p className="text-lg text-custom-text-200 mt-1">
            VJ Startups OS Contributor
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-1 p-6 border border-custom-border-200 rounded-lg bg-custom-background-100">
          <h2 className="text-xl font-semibold mb-4">Reputation</h2>
          <div className="text-4xl font-bold text-primary-100">--</div>
          <div className="text-sm text-custom-text-200 mt-1">Global Rank: #--</div>
        </div>

        <div className="md:col-span-2 p-6 border border-custom-border-200 rounded-lg bg-custom-background-100">
          <h2 className="text-xl font-semibold mb-4">Recent Contributions</h2>
          <ul className="space-y-4">
            <li className="text-custom-text-200">No recent contributions found.</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
