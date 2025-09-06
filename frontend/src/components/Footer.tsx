export function Footer() {
  return (
    <footer className="w-full bg-gradient-to-r from-slate-50 to-gray-50 border-t border-gray-200 mt-auto">
      <div className="mx-auto max-w-screen-2xl px-4 sm:px-6 py-6">
        <div className="flex flex-col lg:flex-row items-center justify-between gap-4">
          {/* Left side - Company info */}
          <div className="flex flex-col sm:flex-row items-center gap-2 text-center sm:text-left">
            <div className="flex items-center gap-2">
              <span className="text-gray-600 text-sm">© {new Date().getFullYear()}</span>
              <span className="font-semibold text-gray-900 text-lg">
                Adārah from Hebron™
              </span>
            </div>
            <div className="hidden lg:block w-px h-4 bg-gray-300"></div>
            <span className="text-gray-600 text-sm">Digital Signage Platform</span>
          </div>
          
          {/* Right side - Tech stack */}
          <div className="flex flex-col sm:flex-row items-center gap-3">
            <span className="text-xs text-gray-500 font-medium">Powered by</span>
            <div className="flex items-center gap-2">
              <span className="bg-blue-50 border border-blue-200 text-blue-700 px-3 py-1 rounded-full text-xs font-semibold">Next.js</span>
              <span className="bg-purple-50 border border-purple-200 text-purple-700 px-3 py-1 rounded-full text-xs font-semibold">Tailwind</span>
              <span className="bg-gray-50 border border-gray-200 text-gray-700 px-3 py-1 rounded-full text-xs font-semibold">shadcn/ui</span>
            </div>
          </div>
        </div>
        
        {/* Bottom row - Additional links */}
        <div className="mt-6 pt-4 border-t border-gray-200 flex flex-col sm:flex-row items-center justify-center gap-6">
          <div className="flex flex-wrap items-center justify-center gap-6 text-sm">
            <a href="/privacy" className="text-gray-600 hover:text-blue-600 transition-colors duration-200 font-medium">Privacy Policy</a>
            <a href="/terms" className="text-gray-600 hover:text-blue-600 transition-colors duration-200 font-medium">Terms of Service</a>
            <a href="/support" className="text-gray-600 hover:text-blue-600 transition-colors duration-200 font-medium">Support</a>
            <a href="/docs" className="text-gray-600 hover:text-blue-600 transition-colors duration-200 font-medium">Documentation</a>
          </div>
        </div>
      </div>
    </footer>
  );
}
