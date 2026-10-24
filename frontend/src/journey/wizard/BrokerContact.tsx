import { useState } from 'react';
import { MessageCircle } from 'lucide-react';
import { Modal } from '../../ui/primitives';
import { journey, openJourney, type IntakeState } from '../api';
import BrokerHandoff from '../BrokerHandoff';

export default function BrokerContact({prepare}:{prepare?:()=>Promise<IntakeState>}) {
 const [open,setOpen]=useState(false);
 async function current(){const state=await openJourney();if(state.version && JSON.stringify(state.profile)===JSON.stringify(state.draft))return state;return journey<IntakeState>('/profile/confirm',{expected_version:state.version,draft_hash:state.draft_hash,source:'manual'});}
 return <><button className="w-broker-float" onClick={()=>setOpen(true)} aria-haspopup="dialog"><MessageCircle size={17}/> Talk to a broker</button><Modal open={open} onClose={()=>setOpen(false)} title="A human can help"><div className="journey"><BrokerHandoff prepare={prepare || current} initiallyOpen/></div></Modal></>;
}
