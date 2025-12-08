// Minimal client-side helpers for static demo site (localStorage-based)
(function(){
  window.seedDemoData = function(email){
    try{
      const key = 'activities_'+email;
      if (localStorage.getItem(key)) return;
      const now = new Date();
      const sample = [
        {description:'Morning run', earnedMinutes:30, createdAt: new Date(now.getTime()-3600*1000*24).toISOString(), source:'strava'},
        {description:'Evening walk', earnedMinutes:15, createdAt: new Date(now.getTime()-3600*1000*10).toISOString(), source:'manual'}
      ];
      localStorage.setItem(key, JSON.stringify(sample));
    }catch(e){console.error(e)}
  };
  // expose simple logout helper
  window.demoLogout = function(){ localStorage.removeItem('move2earn_current'); location.href='index.html'; };
})();
