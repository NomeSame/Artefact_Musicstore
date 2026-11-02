// Original vector instrument illustrations. These are not product photographs.
export function instrument(category, id=0) {
 const colors=["#aa6a36","#a14931","#d5ba7c","#344e43","#c69758","#c9b797"];
 const wood=colors[id%colors.length], dark="#353b32", metal="#d0cbb9";
 let shape="";
 const strings = (x,y,len,count=6,gap=2) => Array.from({length:count},(_,i)=>'<path d="M'+(x+i*gap)+' '+y+'v'+len+'" stroke="#ddd5b5" stroke-width=".6"/>').join("");
 if ([1,2,5,8,9].includes(category)) {
  const acoustic=[5,9].includes(category);
  const bass=category===2, orchestra=category===8;
  shape='<g transform="rotate(25 100 120)">'+
    '<rect x="94" y="26" width="13" height="115" rx="3" fill="#755339"/>'+
    '<path d="M91 8h19v29H91z" fill="'+wood+'"/>'+
    '<path d="M88 12h5m-5 8h5m-5 8h5m15-16h5m-5 8h5m-5 8h5" stroke="'+metal+'" stroke-width="3" stroke-linecap="round"/>'+
    (acoustic ? '<path d="M82 113C54 104 51 137 66 150C37 181 60 215 100 216C140 215 163 181 134 150C149 137 146 104 118 113L110 128H90Z" fill="'+wood+'" stroke="#755637" stroke-width="2"/><path d="M82 122C62 117 62 140 76 151C52 180 69 204 100 205C131 204 148 180 124 151C138 140 138 117 118 122" fill="none" stroke="#dfc48c" stroke-width="2"/><circle cx="100" cy="154" r="15" fill="#34352c" stroke="#cbb880" stroke-width="4"/><path d="M80 185h40v7H80z" fill="#553e2b"/>' :
    orchestra ? '<path d="M83 110C60 105 64 131 78 139C57 152 66 185 100 190C134 185 143 152 122 139C136 131 140 105 117 110L108 120H92Z" fill="'+wood+'" stroke="#68452a" stroke-width="2"/><path d="M86 142q-10 13 0 23m28-23q10 13 0 23" fill="none" stroke="#523e2d" stroke-width="2"/><path d="M91 163h18l-3 30H94Z" fill="'+dark+'"/>' :
    '<path d="M84 113L74 91Q61 89 65 123C31 144 50 202 97 210C143 208 158 177 140 147L122 106Q115 99 114 131L106 140H92Z" fill="'+wood+'" stroke="#444337" stroke-width="2"/><path d="M91 139L114 134L124 170L111 185L84 174Z" fill="'+(bass?"#dddbcc":"#f0ead5")+'"/><rect x="89" y="153" width="23" height="6" rx="2" fill="'+dark+'"/><rect x="88" y="177" width="25" height="5" rx="1" fill="'+metal+'"/><circle cx="126" cy="180" r="4" fill="'+metal+'"/>')+
    '<rect x="95" y="36" width="10" height="'+(acoustic?101:112)+'" fill="#4f4131"/>'+
    Array.from({length:15},(_,i)=>'<path d="M95 '+(40+i*6)+'h10" stroke="#b5ad91" stroke-width=".8"/>').join("")+
    strings(bass?97:95,12,180,bass?4:6,bass?2:2)+'</g>';
 } else if(category===4) {
  shape='<g transform="translate(7 73) rotate(-12 95 50)"><rect x="0" y="0" width="188" height="95" rx="6" fill="'+dark+'"/><rect x="7" y="8" width="174" height="23" rx="2" fill="#4e5548"/><rect x="66" y="13" width="34" height="12" rx="2" fill="#a3b5a2"/>'+Array.from({length:9},(_,i)=>'<circle cx="'+(14+i*15)+'" cy="18" r="2.5" fill="#c0b997"/>').join("")+
    Array.from({length:21},(_,i)=>'<rect x="'+(8+i*8.2)+'" y="40" width="7.5" height="48" rx="1" fill="#f1efdf"/>').join("")+
    Array.from({length:20},(_,i)=>[2,6].includes(i%7)?'':'<rect x="'+(13+i*8.2)+'" y="40" width="5" height="29" rx="1" fill="#252c28"/>').join("")+'</g>';
 } else if(category===3) {
  shape='<g stroke="'+dark+'" stroke-width="3"><path d="M43 69v139m114-139v139M26 209l17-20 17 20m80 0 17-20 17 20" fill="none"/><ellipse cx="43" cy="67" rx="34" ry="6" fill="#c2a45d"/><ellipse cx="157" cy="67" rx="34" ry="6" fill="#c2a45d"/><path d="M62 99v32q18 16 37 0V99m5 0v32q18 16 37 0V99" fill="'+wood+'"/><ellipse cx="81" cy="99" rx="19" ry="7" fill="#e3deca"/><ellipse cx="123" cy="99" rx="19" ry="7" fill="#e3deca"/><circle cx="102" cy="161" r="44" fill="'+wood+'"/><circle cx="102" cy="161" r="37" fill="#e9e4d4"/><circle cx="114" cy="174" r="9" fill="#333c32"/></g>';
 } else {
  const sax=category===6;
  shape='<g transform="rotate(-20 100 125)" fill="'+(sax?"#c1a25d":"#d0b979")+'" stroke="#8d774d" stroke-width="2">'+
   (sax?'<path d="M111 29q-20-20-28 3l-2 113q-3 21 15 21q18 0 14-23l-3-37 31-11 13 42q12 59-40 65q-57 4-55-52l4-108q0-38 40-28Z"/><path d="M108 106l36-11 6 11-39 12Z"/><path d="M111 28l13-3 6 9-16 6Z" fill="#313c32"/>' :
   '<path d="M47 110h90l25-27v71l-25-26H45q-25 0-25 24t26 24h71v-18H46q-8 0-8-7t8-7h85v-20H47Z"/><ellipse cx="164" cy="118" rx="14" ry="36"/><path d="M63 92h9v48h-9zm22 0h9v48h-9zm22 0h9v48h-9Z"/><path d="M58 88h19m3 0h19m3 0h19" stroke-width="5"/>')+'</g>';
 }
 return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 240" aria-hidden="true" focusable="false">'+shape+'</svg>';
}
