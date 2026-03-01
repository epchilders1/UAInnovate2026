import './Button.css';
import { useLoading } from '../../context/LoadingContext';
interface ButtonProps{
    onClick?: any
    label?: string
    children: any
    rounded?: boolean
    manageLoading?: boolean
}


export default function Button(props:ButtonProps){
    const {children, rounded, onClick, manageLoading = true} = props;
    const {setLoading} = useLoading()

    const handleClick = async ()=>{
        if (!onClick) return;
        if (manageLoading) setLoading(true);
        await onClick();
        if (manageLoading) setLoading(false);
    }
    return(
        <button onClick={handleClick} className={`btn-primary ${rounded && 'rounded'}`}>
            {children}
        </button>
    );
}