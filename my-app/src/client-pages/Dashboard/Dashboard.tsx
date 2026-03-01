import './Dashboard.css';
import { useJarvis } from '../../context/JarvisContext';
import { hatch } from 'ldrs'
hatch.register()

export default function Dashboard(){
    const { askingPrompt } = useJarvis();

    return(
        <div className="dashboard-container">
            <p>Dashboard</p>
        </div>
    );
}