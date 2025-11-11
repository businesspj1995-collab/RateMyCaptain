
export enum Base {
    ORD = "ORD",
    IAH = "IAH",
    DEN = "DEN",
    EWR = "EWR",
    SFO = "SFO",
    LAX = "LAX",
    IAD = "IAD",
    GUM = "GUM"
}

export enum Fleet {
    B737 = "737",
    B757 = "757",
    B767 = "767",
    B777 = "777",
    B787 = "787",
    A320 = "A319/A320",
    A321 = "A321neo"
}

export interface Captain {
    id: string;
    name: string;
    base: Base;
    fleet: Fleet;
}

export interface Rating {
    id: string;
    captainId: string;
    professionalism: number; // 1-5
    crm: number; // 1-5
    communication: number; // 1-5
    easeToFlyWith: number; // 1-5
    micromanagement: number; // 1-5
    cabinCrewInteraction: number; // 1-5
    wouldFlyAgain: number; // 1-5
    helpsWithBoxWork: boolean; // Yes/No
    helpsWithWalkarounds: boolean; // Yes/No
    mentorship: number; // 1-5 (not scored)
    socialInteraction: number; // 1-5 (not scored)
    metAtJet: boolean; // Yes/No (not scored)
}

export type Page = 'home' | 'rate' | 'search' | 'profile' | 'leaderboards';
