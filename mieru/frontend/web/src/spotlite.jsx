import React, { useState } from 'react';
import {
  MapPin,
  Search,
  Star,
  Clock,
  Utensils,
  Wind,
  AlertTriangle,
  Navigation,
  Heart,
  Share2,
  Phone,
  Globe,
  Check,
  LocateFixed,
  ChefHat,
  Smile,
  DollarSign,
  Sparkles,
  ToggleLeft,
  ToggleRight,
  Info,
  Map,
  X,
  Crown,
  ArrowRight
} from 'lucide-react';

// --- COMPONENTS ---

// 1. Info Overlay Modal (Glassmorphism)
const InfoOverlay = ({ item, isOpen, onClose }) => {
  return (
    <div className={`overflow-hidden transition-all duration-700 ease-[cubic-bezier(0.34,1.56,0.64,1)] ${isOpen ? 'max-h-96 opacity-100 mb-6' : 'max-h-0 opacity-0 mb-0'}`}>
      <div className="bg-white/80 backdrop-blur-lg rounded-2xl p-5 border border-white/50 shadow-xl mx-1 relative">

        <div className="flex justify-between items-center mb-4 border-b border-black/5 pb-2 relative z-10">
           <h3 className="font-serif text-sm font-bold text-slate-900 flex items-center gap-2 uppercase tracking-widest">
             <Navigation size={14} className="text-blue-600" /> Essentials
           </h3>
           <button onClick={onClose} className="text-slate-500 hover:text-slate-900 transition-colors bg-white/30 p-1 rounded-full">
             <X size={16} />
           </button>
        </div>

        <div className="grid grid-cols-2 gap-4 relative z-10">
          <div className="space-y-1">
            <div className="flex items-center gap-1.5 text-slate-500 mb-0.5">
              <Clock size={12} />
              <span className="text-[10px] font-bold uppercase">Hours</span>
            </div>
            <p className={`text-sm font-bold font-serif ${item.isOpen ? 'text-emerald-700' : 'text-rose-600'}`}>{item.hours}</p>
          </div>

          <div className="space-y-1">
            <div className="flex items-center gap-1.5 text-slate-500 mb-0.5">
              <Phone size={12} />
              <span className="text-[10px] font-bold uppercase">Phone</span>
            </div>
            <p className="text-sm font-medium text-slate-800 truncate">{item.phone}</p>
          </div>

          <div className="col-span-2 space-y-1">
            <div className="flex items-center gap-1.5 text-slate-500 mb-0.5">
              <MapPin size={12} />
              <span className="text-[10px] font-bold uppercase">Address</span>
            </div>
            <p className="text-sm font-medium text-slate-700 leading-snug">{item.address}</p>
          </div>

          <div className="col-span-2 space-y-1">
             <a href={`https://${item.website}`} className="flex items-center justify-between w-full bg-white/40 hover:bg-white/60 p-2 rounded-xl transition-all border border-white/30 shadow-sm group/link">
               <div className="flex items-center gap-2 text-xs font-bold text-slate-600">
                 <Globe size={12} /> Website
               </div>
               <ArrowRight size={12} className="text-slate-400 group-hover/link:text-blue-600 group-hover/link:translate-x-0.5 transition-all" />
             </a>
          </div>
        </div>
      </div>
    </div>
  );
};

// 2. Glassy Detail Tag
const DetailTag = ({ text, type }) => {
  const isPos = type === 'pos';
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-lg text-[10px] font-bold leading-none backdrop-blur-sm transition-all hover:scale-105 border
      ${isPos
        ? 'bg-emerald-100/40 border-emerald-200/50 text-emerald-800'
        : 'bg-rose-100/40 border-rose-200/50 text-rose-800'}
    `}>
      {text}
    </span>
  );
};

// 3. Liquid Bento Card (Detailed)
// 使用 phrase 和 sentiment
const BentoAspectCard = ({ label, icon, data, isMain }) => {
  if (!data) return null;

  const isHigh = data.rating >= 4.0;
  const isLow = data.rating < 3.0;

  const ratingColor = isHigh ? "text-emerald-700" : isLow ? "text-rose-700" : "text-amber-700";

  const gradientBg = isHigh
    ? "bg-gradient-to-br from-emerald-50/80 to-teal-50/30 border-emerald-100/50"
    : isLow
      ? "bg-gradient-to-br from-rose-50/80 to-orange-50/30 border-rose-100/50"
      : "bg-gradient-to-br from-amber-50/80 to-yellow-50/30 border-amber-100/50";

  // Filter using 'sentiment'
  const posKeywords = data.keywords.filter(k => k.sentiment === 'pos').slice(0, 3);
  const negKeywords = data.keywords.filter(k => k.sentiment === 'neg').slice(0, 3);

  return (
    <div className={`
      ${gradientBg} backdrop-blur-sm rounded-2xl p-3 border flex flex-col shadow-sm relative overflow-hidden
      ${isMain ? 'col-span-2' : 'col-span-1'}
    `}>
      <div className="absolute -top-10 -right-10 w-20 h-20 bg-white/30 rounded-full blur-xl pointer-events-none" />

      <div className="flex justify-between items-start mb-2 relative z-10">
        <div className="flex items-center gap-1.5 text-slate-500/90">
          {icon} <span className="text-[10px] font-bold uppercase tracking-wider">{label}</span>
        </div>
        <div className={`text-lg font-bold font-serif leading-none ${ratingColor} drop-shadow-sm`}>
          {data.rating}
        </div>
      </div>

      <div className="flex flex-col gap-1.5 relative z-10">
         {posKeywords.length > 0 && (
           <div className="flex flex-wrap gap-1">
             {/* Use 'phrase' */}
             {posKeywords.map((kw, i) => (
               <DetailTag key={`pos-${i}`} text={kw.phrase} type="pos" />
             ))}
           </div>
         )}

         {negKeywords.length > 0 && (
           <div className="flex flex-wrap gap-1">
             {/* Use 'phrase' */}
             {negKeywords.map((kw, i) => (
               <DetailTag key={`neg-${i}`} text={kw.phrase} type="neg" />
             ))}
           </div>
         )}

         {posKeywords.length === 0 && negKeywords.length === 0 && (
           <span className="text-[9px] text-slate-400 italic">Balanced experience</span>
         )}
      </div>
    </div>
  );
};

// 4. Glass Ticket
const SignatureTicket = ({ name, count, rank }) => {
  let rankColor = "text-slate-300";
  let badgeIcon = null;
  let cardStyle = "bg-white/60 border-white/60";

  if (rank === 1) {
    rankColor = "text-yellow-600";
    badgeIcon = <Crown size={10} className="fill-yellow-400 text-yellow-600" />;
    cardStyle = "bg-yellow-50/40 border-yellow-200/50";
  }
  else if (rank === 2) { rankColor = "text-slate-500"; cardStyle = "bg-slate-50/40 border-slate-200/50"; }
  else if (rank === 3) { rankColor = "text-amber-700"; cardStyle = "bg-orange-50/40 border-orange-200/50"; }

  return (
    <div className={`
      flex-shrink-0 w-36 ${cardStyle} backdrop-blur-md border rounded-2xl p-3 flex flex-col justify-between
      shadow-[0_4px_12px_-2px_rgba(0,0,0,0.05)] snap-start h-20 relative overflow-hidden group hover:shadow-md transition-all
    `}>
      <div className="flex justify-between items-start">
        <div className={`font-serif font-bold text-base leading-none flex items-center gap-1 ${rankColor}`}>
          {badgeIcon} <span>0{rank}</span>
        </div>
        <span className="text-[9px] font-bold text-slate-600 bg-white/50 px-1.5 py-0.5 rounded-full border border-white/50">
          {count} <span className="opacity-50">likes</span>
        </span>
      </div>

      <div className="text-xs font-bold text-slate-800 leading-tight line-clamp-1 mt-auto relative z-10">
        {name}
      </div>
    </div>
  );
};

// 5. Liquid Main Card
// UPDATED: Changed dish.freq back to dish.count
const RestaurantCard = ({ item, index }) => {
  const [showInfo, setShowInfo] = useState(false);

  return (
    <div
      className="
        bg-white/70 backdrop-blur-2xl rounded-[32px] overflow-hidden
        shadow-[0_8px_32px_rgba(0,0,0,0.08)] border border-white/60
        mb-8 mx-auto flex flex-col animate-slideUp relative
      "
      style={{ animationDelay: `${index * 100}ms` }}
    >

      {/* 1. HERO IMAGE */}
      <div className="w-full h-64 relative flex-shrink-0 group cursor-pointer">
        <img src={item.image} alt={item.name} className="w-full h-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-t from-slate-900/80 via-transparent to-transparent" />

        <div className="absolute top-5 left-5">
           <div className="bg-black/40 backdrop-blur-xl text-white text-xs font-bold px-3 py-1.5 rounded-full shadow-lg border border-white/10 flex items-center gap-1.5">
             <Sparkles size={12} className="text-emerald-400 fill-emerald-400" /> {item.matchScore}% Match
           </div>
        </div>

        <button
          onClick={(e) => { e.stopPropagation(); setShowInfo(!showInfo); }}
          className={`
            absolute top-5 right-5 w-10 h-10 backdrop-blur-md rounded-full flex items-center justify-center
            border-2 border-white/20 transition-all duration-300 shadow-lg
            ${showInfo
              ? 'bg-slate-800 text-white rotate-180 shadow-inner'
              : 'bg-black/30 text-white hover:bg-black/50'}
          `}
        >
          {showInfo ? <X size={18} /> : <Info size={18} />}
        </button>

        <div className="absolute bottom-0 left-0 w-full p-6 text-white">
           <div className="w-full pr-12">
              <h3 className="font-serif text-3xl font-bold leading-tight mb-2 shadow-black drop-shadow-md tracking-wide">
                {item.name}
              </h3>
              <div className="flex items-center gap-3 text-xs font-medium text-slate-100/90">
                <span className="flex items-center gap-1 font-bold text-slate-900 bg-white/90 px-2 py-0.5 rounded-lg backdrop-blur-md shadow-lg">
                  <Star size={10} className="fill-yellow-400 text-yellow-400" /> {item.rating}
                </span>
                <span className="bg-black/20 px-2 py-0.5 rounded-lg backdrop-blur-sm border border-white/10">{item.priceLevel}</span>
                <span className="bg-black/20 px-2 py-0.5 rounded-lg backdrop-blur-sm border border-white/10">{item.distance}</span>
              </div>
           </div>
        </div>
      </div>

      {/* 2. CONTENT BODY */}
      <div className="flex-1 p-6 flex flex-col pt-8 relative">

        <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-b from-white/40 to-white/10 pointer-events-none" />

        <div className="relative z-10">
          <InfoOverlay item={item} isOpen={showInfo} onClose={() => setShowInfo(false)} />
        </div>

        {/* SECTION 1: Ranked Signatures */}
        <div className="mb-8 relative z-10">
          <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3 flex items-center gap-1.5 pl-1">
             <ChefHat size={12} /> Top Signatures
          </h4>
          <div className="flex gap-3 overflow-x-auto scrollbar-hide pb-4 -mx-6 px-6 snap-x">
             {/* UPDATED: Changed back to dish.count */}
             {item.signatures.map((dish, idx) => (
               <SignatureTicket key={idx} rank={idx + 1} name={dish.name} count={dish.count} />
             ))}
          </div>
        </div>

        {/* SECTION 2: Deep Analysis */}
        <div className="mb-8 relative z-10">
           <div className="flex justify-between items-center mb-4 px-1">
              <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Deep Analysis</h4>
              <span className="text-[9px] font-bold text-indigo-500 bg-indigo-50/50 border border-indigo-100 px-2 py-0.5 rounded-full backdrop-blur-sm">AI Generated</span>
           </div>

           <div className="grid grid-cols-2 gap-3">
             <BentoAspectCard isMain={true} label="Taste" icon={<Utensils size={14} />} data={item.aspects.taste} />
             <BentoAspectCard label="Value" icon={<DollarSign size={14} />} data={item.aspects.price} />
             <BentoAspectCard label="Service" icon={<Smile size={14} />} data={item.aspects.service} />
             <BentoAspectCard label="Wait" icon={<Clock size={14} />} data={item.aspects.waiting_time} />
             <BentoAspectCard label="Vibe" icon={<Wind size={14} />} data={item.aspects.environment} />
           </div>
        </div>

        {/* SECTION 3: AI Verdict */}
        <div className="relative z-10 mb-8">
          <div className="pl-5 border-l-2 border-emerald-400/50 py-1 relative">
            <div className="absolute -left-[5px] top-0 w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.8)]"></div>
            <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">Verdict</h4>
            <p className="font-serif text-sm text-slate-700 italic leading-relaxed">
              "{item.ai_summary}"
            </p>
          </div>
        </div>

        {/* SECTION 4: Liquid Button */}
        <button className="
          relative z-10 w-full py-4 rounded-2xl text-sm font-bold flex items-center justify-center gap-2 uppercase tracking-widest
          text-white bg-gradient-to-r from-slate-900 to-slate-800
          shadow-[0_10px_20px_-5px_rgba(0,0,0,0.2)]
          hover:shadow-[0_15px_25px_-5px_rgba(0,0,0,0.3)] hover:-translate-y-0.5
          transition-all active:scale-[0.98] border border-white/10
        ">
          <Map size={16} /> View on Google Map
        </button>

      </div>
    </div>
  );
};

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError(error) { return { hasError: true }; }
  componentDidCatch(error, errorInfo) { console.error(error, errorInfo); }
  render() { if (this.state.hasError) return <h1>Something went wrong.</h1>; return this.props.children; }
}

export default function SpotLite() {
  const [view, setView] = useState('home');
  const [searchQuery, setSearchQuery] = useState('');
  const [isOpenNow, setIsOpenNow] = useState(false);
  const [restaurants, setRestaurants] = useState([]);
  const [error, setError] = useState(null);

  const handleSearch = async (e) => {
    if(e) e.preventDefault();
    if (!searchQuery) return;

    setView('loading');
    setError(null);

    try {
        const response = await fetch('/result.json');

        if (!response.ok) {
            throw new Error('Failed to get result');
        }

        const data = await response.json();

        setTimeout(() => {
            setRestaurants(data);
            setView('results');
        }, 1500);

    } catch (err) {
        console.error("Fetch error:", err);
        setError("Unable to load data.");
        setTimeout(() => setView('home'), 1000);
    }
  };

  // --- SCREENS ---

  const HomeScreen = () => (
    <div className="min-h-screen relative flex flex-col items-center justify-center overflow-hidden bg-black">

      <div className="absolute inset-0 z-0">
        <img
          src="https://images.unsplash.com/photo-1559339352-11d035aa65de?auto=format&fit=crop&q=80&w=1920"
          alt="Liquid Luxury Dining"
          className="w-full h-full object-cover opacity-80"
        />
      </div>

      <div className="absolute inset-0 z-0 backdrop-blur-md bg-black/40" />
      <div className="absolute inset-0 z-0 opacity-20 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] mix-blend-overlay" />
      <div className="absolute inset-0 z-0 bg-gradient-to-b from-black/60 via-transparent to-black/90" />

      <div className="relative z-10 w-full max-w-md px-6 text-center animate-fadeIn">

        <h1 className="font-serif text-6xl font-bold text-transparent bg-clip-text bg-gradient-to-b from-white via-white to-white/70 mb-4 tracking-tight drop-shadow-2xl">
          SpotLite
        </h1>
        <p className="text-white/80 mb-12 text-lg font-medium tracking-wide drop-shadow-lg">
          Dining curated by AI.
        </p>

        <form onSubmit={handleSearch} className="bg-white/10 backdrop-blur-3xl p-2 rounded-[2rem] shadow-[0_8px_32px_rgba(0,0,0,0.5)] border border-white/20 transition-all hover:bg-white/20 hover:scale-[1.01]">
          <div className="relative flex items-center border-b border-white/10 mb-2">
            <MapPin className="text-white/70 ml-4" size={20} />
            <input
              type="text"
              placeholder="Paste Google Maps Link..."
              className="w-full p-4 outline-none text-white bg-transparent placeholder:text-white/50 font-medium text-base"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <button
              type="button"
              onClick={() => setSearchQuery('Current Location: USC Campus')}
              className="mr-2 p-2 text-white/70 hover:text-amber-400 transition-colors"
            >
              <LocateFixed size={20} />
            </button>
          </div>

          <div className="flex items-center justify-between px-4 py-2">
             <button
               type="button"
               onClick={() => setIsOpenNow(!isOpenNow)}
               className="flex items-center gap-2 group"
             >
               <div className={`transition-colors ${isOpenNow ? 'text-amber-400' : 'text-white/60'}`}>
                 {isOpenNow ? <ToggleRight size={28} /> : <ToggleLeft size={28} />}
               </div>
               <span className={`text-xs font-bold tracking-widest uppercase transition-colors ${isOpenNow ? 'text-amber-400' : 'text-white/60'}`}>
                 Open Now
               </span>
             </button>

             <button
                type="submit"
                disabled={!searchQuery}
                className={`px-8 py-3 rounded-xl font-bold tracking-widest text-xs uppercase transition-all shadow-lg border border-white/10
                  ${searchQuery ? 'bg-white text-black hover:bg-amber-50' : 'bg-black/40 text-white/30 cursor-not-allowed'}
                `}
              >
                Analyze
              </button>
          </div>
        </form>
        {error && <p className="text-rose-400 text-sm mt-4 font-bold">{error}</p>}
      </div>
    </div>
  );

  const LoadingScreen = () => (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-slate-50 to-stone-100">
      <div className="w-16 h-16 border-4 border-white/50 border-t-emerald-500 rounded-full animate-spin mb-6 shadow-lg" />
      <h2 className="font-serif text-xl text-slate-900 tracking-wide font-bold">Analyzing Palate...</h2>
    </div>
  );

  const ResultsView = () => (
    <div className="min-h-screen pb-20 relative bg-slate-50">
      <div className="fixed inset-0 bg-gradient-to-br from-stone-100 via-white to-blue-50 pointer-events-none" />
      <div className="fixed inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-10 pointer-events-none"></div>

      <div className="sticky top-0 z-30 px-4 py-4 flex justify-between items-center mb-4 backdrop-blur-xl bg-white/70 border-b border-white/50 shadow-sm">
        <h2 className="font-serif text-xl font-bold text-slate-900">Results</h2>
        <button onClick={() => setView('home')} className="text-[10px] font-bold text-slate-500 uppercase tracking-wider hover:text-slate-900">New Search</button>
      </div>

      <div className="px-4 max-w-xl mx-auto relative z-10">
        <p className="text-xs text-slate-400 uppercase tracking-widest mb-8 text-center flex items-center justify-center gap-2">
          <Sparkles size={12} className="text-amber-500" /> Found {restaurants.filter(r => !isOpenNow || r.isOpen).length} matches
        </p>

        {restaurants.filter(r => !isOpenNow || r.isOpen).map((item, idx) => (
          <RestaurantCard key={item.id} item={item} index={idx} />
        ))}
      </div>
    </div>
  );

  return (
    <ErrorBoundary>
      <>
        <style>{`
          .scrollbar-hide::-webkit-scrollbar { display: none; }
          .scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
          .font-serif { font-family: 'Playfair Display', 'Georgia', serif; }
          @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
          .animate-fadeIn { animation: fadeIn 0.6s ease-out forwards; }
          @keyframes slideUp { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }
          .animate-slideUp { animation: slideUp 0.6s ease-out forwards; }
        `}</style>

        {view === 'home' && <HomeScreen />}
        {view === 'loading' && <LoadingScreen />}
        {view === 'results' && <ResultsView />}
      </>
    </ErrorBoundary>
  );
}